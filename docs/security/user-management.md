# 用户管理与权限

本项目引入用户体系与权限控制，用于隔离业务数据并限定管理员能力。

## 关键点
- 认证：JWT access/refresh token
- 角色：admin / user
- 资源隔离：非管理员仅访问 owner_id 绑定的数据
- 管理能力：仅 admin 可进行用户管理

## 注意事项
- SQLite 的 create_all 不会自动为已有表补列，owner_id 等变更需迁移或重建数据库
