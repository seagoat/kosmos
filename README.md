# kosmos: a olm2django tool

可以查看、检索微软 Outlook 导出的 OLM 邮件存档文件的本地系统（使用 Django 搭建）

A local Django system, used to view and search email data, which imported from Microsoft Outlook OLM archive file

## 背景

微软的 Outlook 可以选择导出邮件存档为外部的 OLM 文件，但是并没有提供官方的浏览工具。
目前只在 Windows 系统发现有收费的软件，其他系统上没有发现。

## 最坑爹的点

MAC OS 上的 Outlook 邮件存储使用的数据库系统，无法指定多个分散的位置
`Windows 版可以指定不同的邮箱文件

MacBookPro 可怜的 128G SSD 存储空间，随着邮件的增多，空间会很快被吞噬完毕。
因此选择把历史邮件导出为 OLM，存储到外置硬盘上。

然而再想查看历史邮件只有一个途径，就是重新导入回 Outlook 中，
但是此时系统 SSD 已经不可能有空间做这个操作了

## 契机

无论是导出的 OLM 文件，还是 Mac OS 系统上的数据库存储系统，微软都没有提供公开的格式资料。
偶然间发现了 olm 的 xml schema 定义: [teverett/OLMReader](https://github.com/teverett/OLMReader/blob/master/src/main/resources/schema/)
因此萌发了这个念头

## 思路

1. 基于 xsd 文件，解析 olm 文件
2. 所有的邮件存储到 local 的 django 数据库中
3. 使用 django 的 admin 做简单的浏览、搜索

## 使用手顺

T.B.D
