SET GLOBAL time_zone = '+08:00';

SET SESSION time_zone = '+08:00';

DROP TABLE IF EXISTS `model_config`;

DROP TABLE IF EXISTS `message`;

DROP TABLE IF EXISTS `conversation`;

CREATE TABLE `conversation` (
    `id` BIGINT AUTO_INCREMENT COMMENT '对话ID',
    `user_id` BIGINT NOT NULL COMMENT '用户ID',
    `title` VARCHAR(200) NOT NULL COMMENT '对话标题',
    `create_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    INDEX idx_conversation_user_id (user_id)
) COMMENT '对话';

CREATE TABLE `message` (
    `id` BIGINT AUTO_INCREMENT COMMENT '消息ID',
    `conversation_id` BIGINT NOT NULL COMMENT '对话ID',
    `sender` VARCHAR(20) NOT NULL COMMENT '发送者',
    `content` LONGTEXT NOT NULL COMMENT '消息内容',
    `timestamp` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '发送时间',
    PRIMARY KEY (`id`),
    FOREIGN KEY (`conversation_id`) REFERENCES `conversation` (`id`) ON DELETE CASCADE,
    INDEX idx_message_conversation_id (`conversation_id`)
) COMMENT '消息';

CREATE TABLE `model_config` (
    `id` BIGINT AUTO_INCREMENT COMMENT '模型配置ID',
    `user_id` BIGINT NOT NULL COMMENT '用户ID',
    `base_url` VARCHAR(500) NOT NULL COMMENT 'URL',
    `model_name` VARCHAR(100) NOT NULL COMMENT '模型名称',
    `encrypted_api_key` TEXT DEFAULT NULL COMMENT '加密后的 API 密钥',
    `create_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    INDEX idx_model_config_user_id (`user_id`)
) COMMENT '用户模型配置';