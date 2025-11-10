# Controller Dependency Inventory

Controller modules currently instantiate services and repositories directly using connections from `desktop_app.core.database.db_manager`. The table below summarizes the wiring for each controller.

| Controller | Services created | Repositories instantiated (directly) | Other direct dependencies |
|------------|-----------------|---------------------------------------|---------------------------|
| `auth_controller` | `AuthService` | `UserRepository`, `SessionRepository` | MongoDB, Neo4j driver, Redis client via `db_manager` |
| `dashboard_controller` | _none_ | `SensorRepository`, `AlertRepository` | MongoDB, Redis client |
| `sensor_controller` | `SensorService`, `AlertService`, `AlertRuleService` | `SensorRepository`, `MeasurementRepository`, `AlertRepository`, `AlertRuleRepository`, `UserRepository` | Cassandra session, MongoDB, Redis client, Neo4j driver |
| `alert_controller` | `AlertService` | `AlertRepository`, `SensorRepository`, `ProcessRepository`, `UserRepository` | MongoDB, Redis client, Neo4j driver |
| `alert_rule_controller` | `AlertRuleService` | `AlertRuleRepository`, `AlertRepository` | MongoDB, Redis client |
| `account_controller` | `AccountService`, `InvoiceService`, `PaymentService` | `AccountRepository`, `InvoiceRepository`, `PaymentRepository`, `ProcessRepository` | MongoDB, Neo4j driver |
| `process_controller` | `ProcessService`, `ScheduledProcessService`, `AlertService`, `AlertRuleService`, `AccountService` | `ProcessRepository`, `MeasurementRepository`, `SensorRepository`, `UserRepository`, `InvoiceRepository`, `AccountRepository`, `AlertRepository`, `AlertRuleRepository`, `ScheduledProcessRepository` | Cassandra session, MongoDB, Neo4j driver, Redis client |
| `maintenance_controller` | `MaintenanceService` | `MaintenanceRepository`, `SensorRepository`, `UserRepository` | MongoDB, Neo4j driver |
| `message_controller` | `MessageService`, `UserService` | `MessageRepository`, `GroupRepository`, `UserRepository`, `AccountRepository` | MongoDB, Neo4j driver |
| `group_controller` | `UserService` | `GroupRepository`, `UserRepository`, `AccountRepository` | MongoDB, Neo4j driver |
| `session_controller` | _none_ | `SessionRepository`, `UserRepository` | MongoDB, Redis client, Neo4j driver |

These mappings will guide the refactor to introduce a centralized service/repository factory layer, so controllers depend only on service interfaces.


