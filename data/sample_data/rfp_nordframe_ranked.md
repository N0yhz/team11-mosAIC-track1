# Báo Cáo Phân Tích & Xếp Hạng Yêu Cầu Khách Hàng: Warehouse Inventory Dashboard

> **Tóm tắt dự án:** NordFrame Logistics GmbH is seeking a web-based real-time inventory dashboard to unify stock tracking across 6 regional warehouses in Germany and Austria, integrating with an existing PostgreSQL database and providing role-based access control.

## Bảng Tổng Hợp Yêu Cầu (Xếp hạng từ 1 đến 5)
- **5**: Must have (Bắt buộc phải có)
- **4**: High priority (Rất quan trọng)
- **3**: Medium priority (Quan trọng vừa phải)
- **2**: Low priority (Ưu tiên thấp)
- **1**: Nice to have (Tùy chọn / Có thì tốt hơn)

| Mã | Yêu Cầu | Phân Loại | Mức Ưu Tiên | Điểm | Lý Do Xếp Hạng |
|:---|:---|:---|:---|:---:|:---|
| **REQ-01** | Web-based Real-time Dashboard | Giao diện & Giám sát kho | `5 - Must have` | **5/5** | This is the core deliverable requested by the client. Without a centralized real-time dashboard, the primary business goal of eliminating scattered spreadsheets and legacy systems cannot be achieved. |
| **REQ-03** | PostgreSQL Database Integration | Tích hợp hệ thống & Dữ liệu | `5 - Must have` | **5/5** | A hard technical constraint specified by the client. Failing to integrate with the existing PostgreSQL database means the system cannot fetch live data and will fail deployment. |
| **REQ-04** | Role-Based Access Control (RBAC) | Bảo mật & Phân quyền | `5 - Must have` | **5/5** | Essential for security, data privacy, and correct operational hierarchy across regional sites. Without proper RBAC, unauthorized users could view sensitive multi-site inventory data. |
| **REQ-02** | Automated Low-Stock Alerts | Cảnh báo & Tự động hóa | `4 - High priority` | **4/5** | Critical for operational efficiency and preventing stockouts, ensuring managers can act quickly. It provides high business value, although the core dashboard view is technically prerequisite. |
| **REQ-05** | Data Migration and Onboarding Plan | Vận hành & Triển khai | `4 - High priority` | **4/5** | Crucial for ensuring the pilot and full rollout succeed within the tight 6-month timeline without disrupting active warehouse operations. |
| **REQ-06** | Support and Maintenance Terms | Hỗ trợ & Bảo trì | `4 - High priority` | **4/5** | The client explicitly includes the first year of support in their budget and timeline. Defined SLAs are necessary to ensure system reliability for inventory decisions. |
| **REQ-07** | Documentation of Assumptions, Limitations, and Risks | Tài liệu kỹ thuật | `3 - Medium priority` | **3/5** | Important standard project governance artifact to manage expectations and risk, especially given that critical inventory decisions will rely on the dashboard. |

## Chi Tiết Từng Yêu Cầu

### [REQ-01] Web-based Real-time Dashboard
- **Phân loại:** Giao diện & Giám sát kho
- **Mức độ ưu tiên:** **5/5** (5 - Must have)
- **Mô tả yêu cầu:** A web-based dashboard showing real-time inventory levels across all 6 warehouses.
- **Lý do đánh giá:** This is the core deliverable requested by the client. Without a centralized real-time dashboard, the primary business goal of eliminating scattered spreadsheets and legacy systems cannot be achieved.

### [REQ-03] PostgreSQL Database Integration
- **Phân loại:** Tích hợp hệ thống & Dữ liệu
- **Mức độ ưu tiên:** **5/5** (5 - Must have)
- **Mô tả yêu cầu:** Integration with our existing PostgreSQL inventory database without migration to a new database.
- **Lý do đánh giá:** A hard technical constraint specified by the client. Failing to integrate with the existing PostgreSQL database means the system cannot fetch live data and will fail deployment.

### [REQ-04] Role-Based Access Control (RBAC)
- **Phân loại:** Bảo mật & Phân quyền
- **Mức độ ưu tiên:** **5/5** (5 - Must have)
- **Mô tả yêu cầu:** Role-based access allowing warehouse managers to only see their own site, while HQ staff see all sites.
- **Lý do đánh giá:** Essential for security, data privacy, and correct operational hierarchy across regional sites. Without proper RBAC, unauthorized users could view sensitive multi-site inventory data.

### [REQ-02] Automated Low-Stock Alerts
- **Phân loại:** Cảnh báo & Tự động hóa
- **Mức độ ưu tiên:** **4/5** (4 - High priority)
- **Mô tả yêu cầu:** Automated low-stock alerts sent to warehouse managers when items fall below a configurable threshold.
- **Lý do đánh giá:** Critical for operational efficiency and preventing stockouts, ensuring managers can act quickly. It provides high business value, although the core dashboard view is technically prerequisite.

### [REQ-05] Data Migration and Onboarding Plan
- **Phân loại:** Vận hành & Triển khai
- **Mức độ ưu tiên:** **4/5** (4 - High priority)
- **Mô tả yêu cầu:** A data migration and onboarding plan for rolling this out across all 6 sites with minimal disruption.
- **Lý do đánh giá:** Crucial for ensuring the pilot and full rollout succeed within the tight 6-month timeline without disrupting active warehouse operations.

### [REQ-06] Support and Maintenance Terms
- **Phân loại:** Hỗ trợ & Bảo trì
- **Mức độ ưu tiên:** **4/5** (4 - High priority)
- **Mô tả yêu cầu:** Support and maintenance terms after go-live, including response times and SLAs.
- **Lý do đánh giá:** The client explicitly includes the first year of support in their budget and timeline. Defined SLAs are necessary to ensure system reliability for inventory decisions.

### [REQ-07] Documentation of Assumptions, Limitations, and Risks
- **Phân loại:** Tài liệu kỹ thuật
- **Mức độ ưu tiên:** **3/5** (3 - Medium priority)
- **Mô tả yêu cầu:** Clear documentation of any assumptions, limitations, or risks, since inventory decisions will be made based on this system.
- **Lý do đánh giá:** Important standard project governance artifact to manage expectations and risk, especially given that critical inventory decisions will rely on the dashboard.
