#!/usr/libexec/platform-python
# @lint-avoid-python-3-compatibility-imports
#
# pgfaultstacks   Trace page fault stacks and addresses.
#                 For Linux, uses BCC, eBPF.
#
# USAGE: pgfaultstacks [-h] [-p PID [-f]
#                      [--stack-storage-size STACK_STORAGE_SIZE]
#                      [duration]
#
# 04-Aug-2022   Rocky Xing   Created this.

from __future__ import print_function
from bcc import BPF
from sys import stderr
from time import sleep
import argparse
import errno
import signal
import re


pmaps_line_pattern = re.compile(r"""
    (?P<addr_start>[0-9a-f]+)-(?P<addr_end>[0-9a-f]+)\s+  # Address
    (?P<perms>\S+)\s+                                     # Permissions
    (?P<offset>[0-9a-f]+)\s+                              # Map offset
    (?P<dev>\S+)\s+                                       # Device node
    (?P<inode>\d+)\s+                                     # Inode
    (?P<pathname>.*)\s+                                   # Pathname
""", re.VERBOSE)

memory_regions = []


def fill_memory_regions(pid):
    global memory_regions
    with open("/proc/%d/maps" % args.tgid) as f:
        for line in f:
            m = pmaps_line_pattern.match(line)
            if not m:
                continue
            groups = m.groups()
            addr_start = int(groups[0], base=16)
            addr_end = int(groups[1], base=16)
            memory_regions.append([addr_start, addr_end])


def find_memory_region(addr):
    global memory_regions
    for region in memory_regions:
        if region[0] <= addr and addr <= region[1]:
            return True
    return False


def pid_to_comm(tgid, pid):
    try:
        comm = open("/proc/%d/task/%d/comm" % (tgid, pid), "r").read()
        return comm.rstrip()
    except IOError:
        return "--"


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
    ./pgfaultstacks             # trace page faults until Ctrl-C
    ./pgfaultstacks 5           # trace for 5 seconds only
    ./pgfaultstacks -f 5        # 5 seconds, and output in folded format
    ./pgfaultstacks -p 185      # only trace threads for PID 185
"""
parser = argparse.ArgumentParser(
    description="Summarize page faults by stack trace",
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog=examples)
parser.add_argument("-p", "--pid", dest="tgid", required=True,
                          help="trace this PID only", type=positive_int)
parser.add_argument("-f", "--folded", action="store_true",
                    help="output folded format")
parser.add_argument("--stack-storage-size", default=102400,
                    type=positive_nonzero_int,
                    help="the number of unique stack traces that can be stored and displayed")
parser.add_argument("--ebpf", action="store_true",
                    help=argparse.SUPPRESS)
parser.add_argument("duration", nargs="?", default=99999999,
                    help="duration of trace, in seconds")

args = parser.parse_args()
folded = args.folded
duration = int(args.duration)


def signal_ignore(signal, frame):
    print()


bpf_text = """
#include <uapi/linux/ptrace.h>
#include <linux/sched.h>

struct key_t {
    u32 pid;
    int user_stack_id;
    u64 address;
};

BPF_HASH(page_faults, struct key_t, u8, 1000000);
BPF_STACK_TRACE(stack_traces, STACK_STORAGE_SIZE);
"""

bpf_text_tracepoint = """
TRACEPOINT_PROBE(exceptions, page_fault_user)
{
    // user, write, not-present
    if (args->error_code != 0x6) {
        return 0;
    }

    u64 address = args->address;
    struct pt_regs *ctx = (struct pt_regs *)args;
    u32 pid = bpf_get_current_pid_tgid();
    u32 tgid = bpf_get_current_pid_tgid() >> 32;

    if (!(THREAD_FILTER)) {
        return 0;
    }

    u8 val = 1;
    struct key_t key = {};
    key.pid = pid;
    key.user_stack_id = stack_traces.get_stackid(ctx, BPF_F_USER_STACK);
    key.address = address;
    page_faults.update(&key, &val);

    return 0;
}
"""

bpf_text_kprobe = """
int kprobe__handle_mm_fault(struct pt_regs *ctx, struct vm_area_struct *vma, unsigned long address)
{
    u32 pid = bpf_get_current_pid_tgid();
    u32 tgid = bpf_get_current_pid_tgid() >> 32;

    if (!(THREAD_FILTER)) {
        return 0;
    }

    u8 val = 1;
    struct key_t key = {};
    key.pid = pid;
    key.user_stack_id = stack_traces.get_stackid(ctx, BPF_F_USER_STACK);
    key.address = (u64)address;
    page_faults.update(&key, &val);

    return 0;
}
"""

if BPF.tracepoint_exists("exceptions", "page_fault_user"):
    bpf_text += bpf_text_tracepoint
else:
    bpf_text += bpf_text_kprobe

thread_filter = 'tgid == %d' % args.tgid
bpf_text = bpf_text.replace('THREAD_FILTER', thread_filter)
bpf_text = bpf_text.replace('STACK_STORAGE_SIZE', str(args.stack_storage_size))

if args.ebpf:
    print(bpf_text)
    exit()

b = BPF(text=bpf_text)

if not folded:
    print("Tracing page faults of PID %d by user stack" % args.tgid, end="")
    if duration < 99999999:
        print(" for %d seconds." % duration)
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
page_faults = b.get_table("page_faults")
stack_traces = b.get_table("stack_traces")
aggmap = {}
pidmap = {}

fill_memory_regions(args.tgid)

for k, v in page_faults.items():
    if not find_memory_region(k.address):
        continue
    new_k = (k.pid, k.user_stack_id)
    if new_k in aggmap:
        aggmap[new_k] += 1
    else:
        aggmap[new_k] = 1

for k, v in sorted(aggmap.items(), key=lambda x: x[1]):
    pid, user_stack_id = k[0], k[1]
    comm = pidmap.get(pid)
    if comm is None:
        comm = pid_to_comm(args.tgid, pid)
        pidmap[pid] = comm

    if (user_stack_id < 0 and user_stack_id != -errno.EFAULT):
        missing_stacks += 1
        if user_stack_id == -errno.ENOMEM:
            has_enomem = True
        continue

    user_stack = list(stack_traces.walk(user_stack_id))

    if folded:
        line = [comm] + \
            [b.sym(addr, args.tgid).decode('utf-8', 'replace')
             for addr in reversed(user_stack)]
        print("%s %d" % (";".join(line), v))
    else:
        for addr in user_stack:
            print("    %s" % b.sym(addr, args.tgid).decode('utf-8', 'replace'))
        print("    %-16s %s (%d)" % ("-", comm, pid))
        print("        %d\n" % v)

if missing_stacks > 0:
    enomem_str = "" if not has_enomem else \
        " Consider increasing --stack-storage-size."
    print("WARNING: %d stack traces could not be displayed.%s" %
          (missing_stacks, enomem_str),
          file=stderr)
