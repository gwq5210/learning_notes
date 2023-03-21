#!/usr/bin/python3
# @lint-avoid-python-3-compatibility-imports
#
# memstacks    Trace unfreed or all malloc() stacks and total bytes.
#              For Linux, uses BCC, eBPF.
#
# USAGE: memstacks [-h] [-p PID | -t TID] [-f] [-a] [-O OBJECT]
#                  [--stack-storage-size STACK_STORAGE_SIZE]
#                  [duration]
#
# 28-Jul-2022   Rocky Xing   Created this.

from __future__ import print_function
from bcc import BPF
from sys import stderr
from time import sleep
import argparse
import errno
import signal


def positive_int(val):
    try:
        ival = int(val)
    except ValueError:
        raise argparse.ArgumentTypeError("must be an integer")

    if ival < 0:
        raise argparse.ArgumentTypeError("must be positive")
    return ival


def positive_nonzero_int(val):
    ival = positive_int(val)
    if ival == 0:
        raise argparse.ArgumentTypeError("must be nonzero")
    return ival


examples = """examples:
    ./memstacks             # trace unfreed malloc() bytes until Ctrl-C
    ./memstacks 5           # trace for 5 seconds only
    ./memstacks -f 5        # 5 seconds, and output in folded format
    ./memstacks -p 185      # only trace threads for PID 185
    ./memstacks -t 188      # only trace thread 188
    ./memstacks -a          # trace all malloc() bytes until Ctrl-C
"""
parser = argparse.ArgumentParser(
    description="Summarize unfreed or all malloc() bytes by stack trace",
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog=examples)
thread_group = parser.add_mutually_exclusive_group()
thread_group.add_argument("-p", "--pid", metavar="PID", dest="tgid",
                          help="trace this PID only", type=positive_int)
thread_group.add_argument("-t", "--tid", metavar="TID", dest="pid",
                          help="trace this TID only", type=positive_int)
parser.add_argument("-f", "--folded", action="store_true",
                    help="output folded format")
parser.add_argument("-a", "--all", action="store_true",
                    help="trace all malloc() bytes")
parser.add_argument("-O", "--object", type=str, default="c",
                    help="attach to allocator functions in the specified object")
parser.add_argument("--stack-storage-size", default=10240,
                    type=positive_nonzero_int,
                    help="the number of unique stack traces that can be stored and "
                    "displayed (default 10240)")
parser.add_argument("--ebpf", action="store_true",
                    help=argparse.SUPPRESS)
parser.add_argument("duration", nargs="?", default=99999999,
                    type=positive_nonzero_int,
                    help="duration of trace, in seconds")

args = parser.parse_args()
if args.pid and args.tgid:
    parser.error("specify only one of -p and -t")
folded = args.folded
object = args.object
duration = int(args.duration)


def signal_ignore(signal, frame):
    print()


bpf_text = """
#include <uapi/linux/ptrace.h>
#include <linux/sched.h>

struct key_t {
    u32 pid;
    u32 tgid;
    int user_stack_id;
    char name[TASK_COMM_LEN];
};

BPF_HASH(bytes, struct key_t);
BPF_STACK_TRACE(stack_traces, STACK_STORAGE_SIZE);
"""

all_mallocs_text = """
int malloc_enter(struct pt_regs *ctx, size_t size) {
    u32 pid = bpf_get_current_pid_tgid();
    u32 tgid = bpf_get_current_pid_tgid() >> 32;

    if (!(THREAD_FILTER)) {
        return 0;
    }

    u64 *val, zero = 0;
    struct key_t key = {};
    key.pid = pid;
    key.tgid = tgid;
    key.user_stack_id = stack_traces.get_stackid(ctx, BPF_F_USER_STACK);
    bpf_get_current_comm(&key.name, sizeof(key.name));
    val = bytes.lookup_or_init(&key, &zero);
    // val = bytes.lookup_or_try_init(&key, &zero);
    if (val) {
        (*val) += size;
    }

    return 0;
}
"""

unfreed_mallocs_text = """
struct alloc_info_t {
    u32 pid;
    u64 address;
};

struct alloc_val_t {
    u64 size;
    int user_stack_id;
};

BPF_HASH(sizes, u64);
BPF_HASH(allocs, struct alloc_info_t, struct alloc_val_t, 1000000);

int malloc_enter(struct pt_regs *ctx, size_t size) {
    u32 pid = bpf_get_current_pid_tgid();
    u32 tgid = bpf_get_current_pid_tgid() >> 32;

    if (!(THREAD_FILTER)) {
        return 0;
    }

    u64 pid64 = pid;
    u64 size64 = size;
    sizes.update(&pid64, &size64);

    return 0;
}

int malloc_exit(struct pt_regs *ctx) {
    u32 pid = bpf_get_current_pid_tgid();
    u32 tgid = bpf_get_current_pid_tgid() >> 32;

    if (!(THREAD_FILTER)) {
        return 0;
    }

    u64 pid64 = pid;
    u64 *size64 = sizes.lookup(&pid64);
    if (!size64) {
        return 0; // missed malloc entry
    }

    struct alloc_info_t alloc_info = {};
    struct alloc_val_t alloc_val = {};
    alloc_info.pid = pid;
    alloc_info.address = PT_REGS_RC(ctx);
    alloc_val.size = *size64;
    alloc_val.user_stack_id = stack_traces.get_stackid(ctx, BPF_F_USER_STACK);
    allocs.update(&alloc_info, &alloc_val);
    sizes.delete(&pid64);

    u64 *val, zero = 0;
    struct key_t key = {};
    key.pid = pid;
    key.tgid = tgid;
    key.user_stack_id = alloc_val.user_stack_id;
    bpf_get_current_comm(&key.name, sizeof(key.name));
    val = bytes.lookup_or_init(&key, &zero);
    // val = bytes.lookup_or_try_init(&key, &zero);
    if (val) {
        (*val) += *size64;
    }

    return 0;
}

int free_enter(struct pt_regs *ctx, void *ptr) {
    u32 pid = bpf_get_current_pid_tgid();
    u32 tgid = bpf_get_current_pid_tgid() >> 32;

    if (!(THREAD_FILTER)) {
        return 0;
    }

    struct alloc_info_t alloc_info = {};
    alloc_info.pid = pid;
    alloc_info.address = (u64)ptr;
    struct alloc_val_t *alloc_val = allocs.lookup(&alloc_info);
    if (!alloc_val) {
        return 0;
    }
    
    struct key_t key = {};
    key.pid = pid;
    key.tgid = tgid;
    key.user_stack_id = alloc_val->user_stack_id;
    bpf_get_current_comm(&key.name, sizeof(key.name));
    u64 *val = bytes.lookup(&key);
    if (val) {
        (*val) -= alloc_val->size;
        if (*val <= 0) {
            bytes.delete(&key);
        }
    }

    allocs.delete(&alloc_info);

    return 0;
}
"""

if args.all:
    bpf_text += all_mallocs_text
else:
    bpf_text += unfreed_mallocs_text

thread_context = ""
if args.tgid is not None:
    thread_context = "PID %d" % args.tgid
    thread_filter = 'tgid == %d' % args.tgid
elif args.pid is not None:
    thread_context = "TID %d" % args.pid
    thread_filter = 'pid == %d' % args.pid
else:
    thread_context = "all threads"
    thread_filter = '1'
bpf_text = bpf_text.replace('THREAD_FILTER', thread_filter)
bpf_text = bpf_text.replace('STACK_STORAGE_SIZE', str(args.stack_storage_size))

if args.ebpf:
    print(bpf_text)
    exit()

b = BPF(text=bpf_text)
if args.pid is not None:
    tpid = args.pid
else:
    tpid = -1

b.attach_uprobe(name=object, sym="malloc", fn_name="malloc_enter", pid=tpid)
if not args.all:
    b.attach_uretprobe(name=object, sym="malloc",
                       fn_name="malloc_exit", pid=tpid)
    b.attach_uprobe(name=object, sym="free", fn_name="free_enter", pid=tpid)

matched = b.num_open_uprobes()
if matched == 0:
    print("error: 0 functions traced. Exiting.", file=stderr)
    exit(1)

if not folded:
    trace_mode = "all" if args.all else "unfreed"
    print("Tracing %s malloc() bytes of %s by user stack" %
          (trace_mode, thread_context), end="")
    if duration < 99999999:
        print(" for %d secs." % duration)
    else:
        print("... Hit Ctrl-C to end.")

try:
    sleep(duration)
except KeyboardInterrupt:
    signal.signal(signal.SIGINT, signal_ignore)

if not folded:
    print()

missing_stacks = 0
has_enomem = False
bytemap = b.get_table("bytes")
stack_traces = b.get_table("stack_traces")
for k, v in sorted(bytemap.items(), key=lambda bytemap: bytemap[1].value):
    if (k.user_stack_id < 0 and k.user_stack_id != -errno.EFAULT):
        missing_stacks += 1
        if k.user_stack_id == -errno.ENOMEM:
            has_enomem = True
        continue

    user_stack = list(stack_traces.walk(k.user_stack_id))

    if folded:
        line = [k.name.decode()] + \
            [b.sym(addr, k.tgid, show_module=True, show_offset=True).decode(
                'utf-8', 'replace') for addr in reversed(user_stack)]
        print("%s %d" % (";".join(line), v.value))
    else:
        for addr in user_stack:
            print("    %s" % b.sym(addr, k.tgid, show_module=True,
                  show_offset=True).decode('utf-8', 'replace'))
        print("    %-16s %s (%d)" % ("-", k.name.decode(), k.pid))
        print("        %d\n" % v.value)

if missing_stacks > 0:
    enomem_str = "" if not has_enomem else \
        " Consider increasing --stack-storage-size."
    print("WARNING: %d stack traces could not be displayed.%s" %
          (missing_stacks, enomem_str),
          file=stderr)

