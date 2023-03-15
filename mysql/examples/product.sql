use test;
CREATE TABLE `product`  (
  `id` int(11) NOT NULL,
  `product_no` varchar(20)  DEFAULT NULL,
  `count` int(11) NOT NULL,
  `count2` int(11) NOT NULL,
  `name` varchar(255) DEFAULT NULL,
  `price` decimal(10, 2) DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

CREATE INDEX idx_id_product_no ON product(id,product_no);
CREATE INDEX idx_product_no_count ON product(product_no, count);
CREATE INDEX idx_count_count2 ON product(count, count2);

insert into product values(1, '0001', 1, 1, 'apple1', 5);
insert into product values(2, '0002', 1, 4, 'applex2', 5);
insert into product values(4, '0004', 4, 1, 'apple3', 5);
insert into product values(5, '0005', 4, 4, 'apple3', 5);
insert into product values(8, '0008', 8, 8, 'applex4', 5);
insert into product values(9, '0009', 9, 9, 'applex5', 5);
insert into product values(10, '0010', 10, 1, 'applex6', 5);
insert into product values(11, '0011', 11, 10, 'applex6', 5);
insert into product values(12, '0011', 11, 10, 'applex6', 5);