"""
Session history widget for administrators.
"""
from typing import Dict, Optional, List
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGroupBox,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QMessageBox,
)
from PyQt6.QtCore import Qt

from desktop_app.controllers import get_session_controller

class SessionHistoryWidget(QWidget):
    """Widget that displays historical session activity."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.session_controller = get_session_controller()

        self._users_cache: Dict[str, Dict[str, str]] = {}

        self._init_ui()
        self._load_users()
        self.load_sessions()

    def _init_ui(self) -> None:
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        header_layout = QHBoxLayout()
        title = QLabel("Historial de Sesiones")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        refresh_btn = QPushButton("Actualizar")
        refresh_btn.clicked.connect(self.load_sessions)
        header_layout.addWidget(refresh_btn)
        layout.addLayout(header_layout)

        filter_group = QGroupBox("Filtros")
        filter_layout = QHBoxLayout()

        filter_layout.addWidget(QLabel("Usuario:"))
        self.user_combo = QComboBox()
        self.user_combo.currentIndexChanged.connect(self.load_sessions)
        filter_layout.addWidget(self.user_combo)

        filter_layout.addStretch()
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            [
                "Usuario",
                "Email",
                "Rol",
                "Inicio de sesión",
                "Cierre de sesión",
                "Duración",
            ]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

        self.setLayout(layout)

    def _load_users(self) -> None:
        self.user_combo.clear()
        self.user_combo.addItem("Todos los usuarios", None)

        try:
            users = self.session_controller.list_users(skip=0, limit=1000)
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar los usuarios: {exc}")
            return

        self._users_cache = {}
        for user in sorted(users, key=lambda u: u.nombre_completo.lower()):
            display = f"{user.nombre_completo} ({user.email})"
            self.user_combo.addItem(display, user.id)
            self._users_cache[user.id] = {
                "nombre": user.nombre_completo,
                "email": user.email,
            }

    def load_sessions(self) -> None:
        selected_user_id = self.user_combo.currentData()

        try:
            sessions = self.session_controller.get_session_history(
                user_id=selected_user_id,
                skip=0,
                limit=200,
            )
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"No se pudo obtener el historial: {exc}")
            self.table.setRowCount(0)
            return

        if not sessions:
            self.table.setRowCount(0)
            return

        self.table.setRowCount(len(sessions))

        for row, session in enumerate(sessions):
            user_info = self._users_cache.get(session.get("user_id")) or self._fetch_user(
                session.get("user_id")
            )

            nombre = user_info.get("nombre", "Desconocido")
            email = user_info.get("email", "N/D")
            rol = session.get("role", "N/D")

            login_time = self._format_datetime(session.get("login_time"))
            logout_time_raw = session.get("logout_time")
            logout_time = self._format_datetime(logout_time_raw)

            duration = self._calculate_duration(session.get("login_time"), logout_time_raw)

            self.table.setItem(row, 0, QTableWidgetItem(nombre))
            self.table.setItem(row, 1, QTableWidgetItem(email))
            self.table.setItem(row, 2, QTableWidgetItem(rol))
            self.table.setItem(row, 3, QTableWidgetItem(login_time))
            self.table.setItem(row, 4, QTableWidgetItem(logout_time or "Activa"))
            self.table.setItem(row, 5, QTableWidgetItem(duration))

    def _fetch_user(self, user_id: Optional[str]) -> Dict[str, str]:
        if not user_id:
            return {}
        try:
            user = self.session_controller.get_user(user_id)
        except Exception:
            user = None

        if not user:
            info = {"nombre": "Desconocido", "email": "N/D"}
        else:
            info = {"nombre": user.nombre_completo, "email": user.email}

        self._users_cache[user_id] = info
        return info

    @staticmethod
    def _format_datetime(value: Optional[datetime]) -> str:
        if not value:
            return ""
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return value
        return value.strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def _calculate_duration(
        login_time: Optional[datetime], logout_time: Optional[datetime]
    ) -> str:
        if not login_time:
            return "N/D"

        if isinstance(login_time, str):
            try:
                login_time = datetime.fromisoformat(login_time.replace("Z", "+00:00"))
            except ValueError:
                return "N/D"

        if logout_time:
            if isinstance(logout_time, str):
                try:
                    logout_time = datetime.fromisoformat(logout_time.replace("Z", "+00:00"))
                except ValueError:
                    logout_time = None
        else:
            logout_time = datetime.utcnow()

        if not logout_time:
            return "N/D"

        delta = logout_time - login_time
        total_seconds = int(delta.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


