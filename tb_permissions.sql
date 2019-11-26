/*
Navicat MySQL Data Transfer

Source Server         : 本地
Source Server Version : 80016
Source Host           : localhost:3306
Source Database       : hbb_course

Target Server Type    : MYSQL
Target Server Version : 80016
File Encoding         : 65001

Date: 2019-09-29 12:58:46
*/

SET FOREIGN_KEY_CHECKS=0;

-- ----------------------------
-- Table structure for `tb_permissions`
-- ----------------------------
DROP TABLE IF EXISTS `tb_permissions`;
CREATE TABLE `tb_permissions` (
  `uuid` varchar(64) NOT NULL,
  `createTime` datetime(6) DEFAULT NULL,
  `updateTime` datetime(6) DEFAULT NULL,
  `icon` varchar(255) DEFAULT NULL,
  `method` varchar(15) DEFAULT NULL,
  `url` varchar(1024) DEFAULT NULL,
  `menuName` varchar(128) DEFAULT NULL,
  `remark` varchar(255) DEFAULT NULL,
  `sortNum` int(11) DEFAULT NULL,
  `enable` tinyint(1) NOT NULL,
  `parentUuid_id` varchar(64) DEFAULT NULL,
  PRIMARY KEY (`uuid`),
  KEY `tb_permissions_parentUuid_id_06d097d6_fk_tb_permissions_uuid` (`parentUuid_id`),
  CONSTRAINT `tb_permissions_parentUuid_id_06d097d6_fk_tb_permissions_uuid` FOREIGN KEY (`parentUuid_id`) REFERENCES `tb_permissions` (`uuid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Records of tb_permissions
-- ----------------------------
INSERT INTO `tb_permissions` VALUES ('412d6408e1d211e99f4c54ee756215bb', null, null, 'el-icon-connection', null, '/roles', '角色管理', '角色管理', '4', '1', null);
INSERT INTO `tb_permissions` VALUES ('412d8b19e1d211e99f4c54ee756215bb', null, null, null, null, '/roles/roles', '角色列表', '角色列表', '1', '1', '412d6408e1d211e99f4c54ee756215bb');
INSERT INTO `tb_permissions` VALUES ('412d8b1ae1d211e99f4c54ee756215bb', null, null, null, null, '/roles/userRoles', '用户权限管理', '用户权限管理', '2', '1', '412d6408e1d211e99f4c54ee756215bb');
INSERT INTO `tb_permissions` VALUES ('412d8b1be1d211e99f4c54ee756215bb', null, null, 'el-icon-collection-tag', null, '/LableManageAll', '标签管理', '标签管理', '5', '1', null);
INSERT INTO `tb_permissions` VALUES ('412d8b1ce1d211e99f4c54ee756215bb', null, null, 'el-icon-files', null, '/dividedManagement', '分成管理', '分成管理', '6', '1', null);
INSERT INTO `tb_permissions` VALUES ('412d8b1de1d211e99f4c54ee756215bb', null, null, null, null, '/dividedManagement/classRepreDivideTradeManag', '课代表分成交易管理', '课代表分成交易管理', '1', '1', '412d8b1ce1d211e99f4c54ee756215bb');
INSERT INTO `tb_permissions` VALUES ('412d8b1ee1d211e99f4c54ee756215bb', null, null, null, null, '/dividedManagement/courseRepresManag', '课代表管理', '课代表管理', '2', '1', '412d8b1ce1d211e99f4c54ee756215bb');
INSERT INTO `tb_permissions` VALUES ('412d8b1fe1d211e99f4c54ee756215bb', null, null, null, null, '/dividedManagement/classRepreCashwithdrawManag', '课代表提现交易管理', '课代表提现交易管理', '3', '1', '412d8b1ce1d211e99f4c54ee756215bb');
INSERT INTO `tb_permissions` VALUES ('412d8b20e1d211e99f4c54ee756215bb', null, null, 'el-icon-set-up', null, '/fixedSettings', '固定配置', '固定配置', '7', '1', null);
INSERT INTO `tb_permissions` VALUES ('412d8b21e1d211e99f4c54ee756215bb', null, null, 'el-icon-s-grid', null, '/columnManage', '栏目管理', '栏目管理', '8', '1', null);
INSERT INTO `tb_permissions` VALUES ('412d8b23e1d211e99f4c54ee756215bb', null, null, 'el-icon-document', null, '/orderManage', '订单管理', '订单管理', '9', '1', null);
INSERT INTO `tb_permissions` VALUES ('412d8b24e1d211e99f4c54ee756215bb', null, null, 'el-icon-s-check', null, '/commentCheck', '评论审核', '评论审核', '10', '1', null);
INSERT INTO `tb_permissions` VALUES ('412d8b25e1d211e99f4c54ee756215bb', null, null, 'el-icon-s-flag', null, '/lessionManage', '课程管理', '课程管理', '1', '1', null);
INSERT INTO `tb_permissions` VALUES ('412d8b26e1d211e99f4c54ee756215bb', null, null, null, null, '/lessionManage/seriesLession', '系列课列表', '系列课列表', '2', '1', '412d8b25e1d211e99f4c54ee756215bb');
INSERT INTO `tb_permissions` VALUES ('412db229e1d211e99f4c54ee756215bb', null, null, null, null, '/lessionManage/lessionRecycle', '课程回收站', '课程回收站', '3', '1', '412d8b25e1d211e99f4c54ee756215bb');
INSERT INTO `tb_permissions` VALUES ('412db22ae1d211e99f4c54ee756215bb', null, null, null, null, '/lessionManage/lessionStoreManageAll', '课件库管理', '课件库管理', '4', '1', '412d8b25e1d211e99f4c54ee756215bb');
INSERT INTO `tb_permissions` VALUES ('412db22be1d211e99f4c54ee756215bb', null, null, 'el-icon-s-ticket', null, '/couponManage', '优惠券管理', '优惠券管理', '2', '1', null);
INSERT INTO `tb_permissions` VALUES ('412db22ce1d211e99f4c54ee756215bb', null, null, 'el-icon-s-custom', null, '/userManage', '用户管理', '用户管理', '3', '1', null);
INSERT INTO `tb_permissions` VALUES ('412db22de1d211e99f4c54ee756215bb', null, null, null, null, '/userManage/userList', '用户列表', '用户列表', '1', '1', '412db22ce1d211e99f4c54ee756215bb');
INSERT INTO `tb_permissions` VALUES ('412db22ee1d211e99f4c54ee756215bb', null, null, null, null, '/userManage/specialist', '专家列表', '专家列表', '2', '1', '412db22ce1d211e99f4c54ee756215bb');
INSERT INTO `tb_permissions` VALUES ('679b5bb6ea8d11e99c3054ee756215bb', null, null, null, null, '/orderManage/orderManage', '订单列表', '订单列表', '1', '1', '412d8b23e1d211e99f4c54ee756215bb');
INSERT INTO `tb_permissions` VALUES ('6bed87f9ea8d11e99c3054ee756215bb', null, null, null, null, '/orderManage/refoundManage', '退款管理', '退款管理', '2', '1', '412d8b23e1d211e99f4c54ee756215bb');
INSERT INTO `tb_permissions` VALUES ('baa85290e27511e99f4c54ee756215bb', null, null, null, null, '/lessionManage/singleLession', '单次课程列表', '单次课程列表', '1', '1', '412d8b25e1d211e99f4c54ee756215bb');