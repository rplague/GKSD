#!/bin/bash

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}
# 切换到安全目录
SAFE_DIR="/tmp"
cd "$SAFE_DIR"
# 显示标题
echo "=========================================="
echo "  Git 安全目录批量配置工具"
echo "=========================================="
echo

# 检查是否以 root 运行
if [[ $EUID -eq 0 ]]; then
    log_warning "脚本正在以 root 用户运行"
else
    log_error "此脚本需要 root 权限来为其他用户配置 Git"
    echo "请使用 sudo 运行此脚本: sudo $0"
    exit 1
fi

# 函数：显示可用用户组
show_available_groups() {
    log_info "可用的用户组:"
    echo "------------------------------------------"
    # 获取所有系统组，排除系统组（GID >= 1000）
    getent group | cut -d: -f1,3 | while IFS=: read name gid; do
        if [[ $gid -ge 1000 ]]; then
            members=$(getent group $name | cut -d: -f4)
            count=$(echo $members | tr ',' ' ' | wc -w)
            echo "  $name (GID: $gid, 成员: $count 人)"
        fi
    done
    echo "------------------------------------------"
}

# 函数：显示现有 Git 仓库
show_existing_repos() {
    local search_dir="$1"
    log_info "在 $search_dir 中查找 Git 仓库..."
    find "$search_dir" -name "*.git" -type d 2>/dev/null | while read repo; do
        if [ -d "$repo/objects" ] && [ -d "$repo/refs" ]; then
            owner=$(stat -c "%U:%G" "$repo")
            permissions=$(stat -c "%a" "$repo")
            echo "  $repo (所有者: $owner, 权限: $permissions)"
        fi
    done
}

# 函数：验证 Git 仓库
validate_git_repo() {
    local repo_path="$1"
    if [[ ! -d "$repo_path" ]]; then
        log_error "目录不存在: $repo_path"
        return 1
    fi
    
    if [[ ! -d "$repo_path/objects" ]] || [[ ! -d "$repo_path/refs" ]]; then
        log_error "这不是一个有效的 Git 仓库: $repo_path"
        return 1
    fi
    
    return 0
}

# 函数：配置单个用户的安全目录
configure_user_safe_directory() {
    local username="$1"
    local repo_path="$2"
    
    # 检查用户是否存在
    if ! id "$username" &>/dev/null; then
        log_error "用户不存在: $username"
        return 1
    fi
    
    # 检查用户是否有家目录
    local user_home=$(eval echo ~$username)
    if [[ ! -d "$user_home" ]]; then
        log_warning "用户 $username 的家目录不存在，跳过"
        return 1
    fi
    
    # 配置安全目录
    if sudo -u "$username" git config --global --get safe.directory | grep -q "$repo_path"; then
        log_info "用户 $username 已配置过安全目录，跳过"
    else
        if sudo -u "$username" git config --global --add safe.directory "$repo_path"; then
            log_success "为用户 $username 配置安全目录: $repo_path"
        else
            log_error "为用户 $username 配置安全目录失败"
            return 1
        fi
    fi
    
    return 0
}

# 主程序开始

# 1. 选择用户组
echo
show_available_groups

while true; do
    read -p "请输入要配置的用户组名: " group_name
    
    if getent group "$group_name" &>/dev/null; then
        group_members=$(getent group "$group_name" | cut -d: -f4)
        member_count=$(echo $group_members | tr ',' ' ' | wc -w)
        log_info "选择的用户组: $group_name (成员: $member_count 人)"
        break
    else
        log_error "用户组 $group_name 不存在，请重新输入"
    fi
done

# 2. 选择 Git 仓库路径
echo
log_info "搜索常见的 Git 仓库目录..."
common_dirs=("/home" "/git" "/var/git" "/mnt" "/opt")
for dir in "${common_dirs[@]}"; do
    if [[ -d "$dir" ]]; then
        show_existing_repos "$dir"
    fi
done

while true; do
    echo
    read -p "请输入 Git 仓库的完整路径: " repo_path
    
    # 移除可能的尾部斜杠
    repo_path="${repo_path%/}"
    
    if validate_git_repo "$repo_path"; then
        log_success "找到有效的 Git 仓库: $repo_path"
        break
    else
        log_error "无效的 Git 仓库路径，请重新输入"
        log_info "提示: 仓库路径应该以 .git 结尾，并且包含 objects 和 refs 目录"
    fi
done

# 3. 确认配置
echo
log_warning "即将进行以下配置:"
echo "------------------------------------------"
echo "用户组: $group_name"
echo "成员: $group_members"
echo "Git 仓库: $repo_path"
echo "------------------------------------------"

read -p "确认配置？(y/N): " confirm
if [[ ! $confirm =~ ^[Yy]$ ]]; then
    log_info "操作已取消"
    exit 0
fi

# 4. 执行配置
echo
log_info "开始为用户组 $group_name 配置安全目录..."

success_count=0
fail_count=0

# 将逗号分隔的成员列表转换为数组
IFS=',' read -ra members <<< "$group_members"

for member in "${members[@]}"; do
    member=$(echo "$member" | tr -d ' ') # 去除空格
    
    if configure_user_safe_directory "$member" "$repo_path"; then
        ((success_count++))
    else
        ((fail_count++))
    fi
done

# 5. 显示结果
echo
echo "=========================================="
log_info "配置完成！"
echo "------------------------------------------"
log_success "成功配置: $success_count 个用户"
if [[ $fail_count -gt 0 ]]; then
    log_error "失败: $fail_count 个用户"
fi
echo "------------------------------------------"

# 6. 验证配置（可选）
echo
read -p "是否要验证配置？(y/N): " verify_confirm
if [[ $verify_confirm =~ ^[Yy]$ ]]; then
    echo
    log_info "验证配置结果:"
    echo "------------------------------------------"
    for member in "${members[@]}"; do
        member=$(echo "$member" | tr -d ' ')
        if id "$member" &>/dev/null; then
            configured=$(sudo -u "$member" git config --global --get safe.directory | grep "$repo_path" || echo "未配置")
            echo "  $member: $configured"
        fi
    done
    echo "------------------------------------------"
fi

# 7. 使用说明
echo
log_info "使用说明:"
echo "现在组 $group_name 的成员可以使用以下命令克隆仓库:"
echo "  git clone username@yourserver:$repo_path"
echo
log_info "要查看特定用户的配置，可以运行:"
echo "  sudo -u username git config --global --list | grep safe.directory"

echo
log_success "脚本执行完成！"
