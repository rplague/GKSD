#!/bin/bash
# correct_backup_strategy.sh

# 配置参数
BASE_DIR="/secure/backup"
MYSQL_USER="backup_user"
MYSQL_PASSWORD="secure_password"
DATE=$(date +%Y%m%d)
DAY_OF_WEEK=$(date +%u)

# 备份保留天数配置
FULL_BACKUP_RETENTION_DAYS=30    # 全量备份保留30天
INCR_BACKUP_RETENTION_DAYS=15    # 增量备份保留15天

# 创建目录结构
FULL_BACKUP_DIR="$BASE_DIR/full"
INCR_BACKUP_DIR="$BASE_DIR/incremental"
mkdir -p $FULL_BACKUP_DIR $INCR_BACKUP_DIR

# 清理过期备份函数
cleanup_old_backups() {
    echo "$(date): 开始清理过期备份文件"
    
    # 清理过期的全量备份
    if [ -d "$FULL_BACKUP_DIR" ]; then
        echo "$(date): 清理 $FULL_BACKUP_RETENTION_DAYS 天前的全量备份"
        find "$FULL_BACKUP_DIR" -maxdepth 1 -type d -name "20*" -mtime +$FULL_BACKUP_RETENTION_DAYS -exec rm -rf {} \;
        echo "$(date): 全量备份清理完成"
    fi
    
    # 清理过期的增量备份
    if [ -d "$INCR_BACKUP_DIR" ]; then
        echo "$(date): 清理 $INCR_BACKUP_RETENTION_DAYS 天前的增量备份"
        find "$INCR_BACKUP_DIR" -maxdepth 1 -type d -name "20*" -mtime +$INCR_BACKUP_RETENTION_DAYS -exec rm -rf {} \;
        echo "$(date): 增量备份清理完成"
    fi
    
    echo "$(date): 过期备份文件清理完成"
}

backup_full() {
    echo "$(date): 开始全量备份"
    
    # 步骤1：创建备份
    echo "$(date): 执行备份操作..."
    mariabackup --backup \
    --user=$MYSQL_USER --password=$MYSQL_PASSWORD \
    --target-dir=$FULL_BACKUP_DIR/$DATE
    
    if [ $? -ne 0 ]; then
        echo "错误：备份创建失败"
        exit 1
    fi
    
    # 步骤2：准备备份（使数据一致）
    echo "$(date): 准备备份文件..."
    mariabackup --prepare --target-dir=$FULL_BACKUP_DIR/$DATE
    
    if [ $? -ne 0 ]; then
        echo "错误：备份准备失败"
        exit 1
    fi
    
    echo "$(date): 全量备份完成: $FULL_BACKUP_DIR/$DATE"
}

backup_incremental() {
    echo "$(date): 开始增量备份"
    
    # 查找最新的全量备份作为基准
    LATEST_FULL=$(ls -t $FULL_BACKUP_DIR | head -1)
    
    if [ -z "$LATEST_FULL" ]; then
        echo "错误：未找到全量备份，无法执行增量备份"
        exit 1
    fi
    
    # 步骤1：创建增量备份
    echo "$(date): 执行增量备份..."
    mariabackup --backup \
    --user=$MYSQL_USER --password=$MYSQL_PASSWORD \
    --target-dir=$INCR_BACKUP_DIR/$DATE \
    --incremental-basedir=$FULL_BACKUP_DIR/$LATEST_FULL
    
    if [ $? -ne 0 ]; then
        echo "错误：增量备份创建失败"
        exit 1
    fi
    
    # 步骤2：准备增量备份
    echo "$(date): 准备增量备份文件..."
    mariabackup --prepare --target-dir=$FULL_BACKUP_DIR/$LATEST_FULL \
    --incremental-dir=$INCR_BACKUP_DIR/$DATE
    
    if [ $? -ne 0 ]; then
        echo "错误：增量备份准备失败"
        exit 1
    fi
    
    echo "$(date): 增量备份完成: $INCR_BACKUP_DIR/$DATE"
}

# 主备份逻辑
case $DAY_OF_WEEK in
    7)  # 周日执行全量备份
        backup_full
        ;;
    *)  # 周一到周六执行增量备份
        backup_incremental
        ;;
esac

# 执行清理过期备份
cleanup_old_backups

echo "$(date): 备份任务完成" >> $BASE_DIR/backup.log