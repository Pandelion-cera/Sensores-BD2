# Controller to Service Dependency Map

| Controller | Services Utilised |
|------------|-------------------|
| `AuthController` | `AuthService` |
| `DashboardController` | `DashboardService` |
| `SensorController` | `SensorService` |
| `AlertController` | `AlertService`, `SensorService`, `ProcessService`, `UserService` |
| `AlertRuleController` | `AlertRuleService` |
| `MessageController` | `MessageService`, `UserService` |
| `AccountController` | `AccountService`, `InvoiceService`, `PaymentService` |
| `ProcessController` | `ProcessService`, `ScheduledProcessService`, `ProcessSchedulerService` |
| `MaintenanceController` | `MaintenanceService`, `SensorService`, `UserService` |
| `GroupController` | `GroupService`, `UserService` |
| `SessionController` | `SessionService`, `UserService` |

This mapping summarises the current dependency chain after introducing service factories.
Controllers now request pre-wired services via `desktop_app.services.factories`
and no longer instantiate repositories directly.

