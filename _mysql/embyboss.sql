-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- 主机： mysql:3306
-- 生成日期： 2023-05-29 07:26:26
-- 服务器版本： 5.7.42
-- PHP 版本： 8.1.17

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- 数据库： `embyboss`
--

-- --------------------------------------------------------

--
-- 表的结构 `emby`
--

CREATE TABLE `emby` (
  `tg` bigint(255) NOT NULL,
  `embyid` char(255) DEFAULT NULL,
  `name` char(255) CHARACTER SET utf8mb4 DEFAULT NULL,
  `pwd` char(255) DEFAULT NULL,
  `pwd2` char(255) CHARACTER SET utf8mb4 DEFAULT NULL,
  `lv` char(255) CHARACTER SET utf8mb4 NOT NULL,
  `cr` datetime DEFAULT NULL,
  `ex` datetime DEFAULT NULL,
  `us` int(255) NOT NULL DEFAULT '0',
  `iv` int(255) DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- 表的结构 `invite`
--

CREATE TABLE `invite` (
  `id` char(255) NOT NULL,
  `tg` int(255) DEFAULT NULL,
  `us` int(255) DEFAULT NULL,
  `used` int(11) DEFAULT NULL,
  `usedtime` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- 转储表的索引
--

--
-- 表的索引 `emby`
--
ALTER TABLE `emby`
  ADD PRIMARY KEY (`tg`);

--
-- 表的索引 `invite`
--
ALTER TABLE `invite`
  ADD PRIMARY KEY (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
