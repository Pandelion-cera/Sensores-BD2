"""
Invoices widget for viewing invoices
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QGroupBox,
    QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from datetime import datetime

from desktop_app.controllers import get_account_controller
from desktop_app.utils.session_manager import SessionManager
from desktop_app.models.invoice_models import InvoiceStatus


class InvoicesWidget(QWidget):
    """Widget for viewing invoices"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.session_manager = SessionManager.get_instance()
        self.account_controller = get_account_controller()
        self.init_ui()
        self.load_invoices()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Facturas")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        # Account summary
        self.account_group = QGroupBox("Resumen de Cuenta")
        account_layout = QVBoxLayout()
        self.account_label = QLabel("Cargando información de cuenta...")
        account_layout.addWidget(self.account_label)
        self.account_group.setLayout(account_layout)
        layout.addWidget(self.account_group)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", "Fecha", "Artículos", "Total", "Estado", "Fecha de Vencimiento"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)
        
        # Buttons
        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("Actualizar")
        refresh_btn.clicked.connect(self.load_invoices)
        btn_layout.addWidget(refresh_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def load_invoices(self):
        try:
            user_id = self.session_manager.get_user_id()
            if not user_id:
                QMessageBox.warning(self, "Error", "Usuario no conectado")
                return
            
            # Load invoices
            invoices = self.account_controller.list_invoices(user_id, skip=0, limit=100)
            
            # Update table
            self.table.setRowCount(len(invoices))
            for row, invoice in enumerate(invoices):
                self.table.setItem(row, 0, QTableWidgetItem(str(invoice.id)))
                
                fecha_str = ""
                if invoice.fecha_emision:
                    if isinstance(invoice.fecha_emision, datetime):
                        fecha_str = invoice.fecha_emision.strftime("%Y-%m-%d")
                    else:
                        fecha_str = str(invoice.fecha_emision)
                self.table.setItem(row, 1, QTableWidgetItem(fecha_str))
                
                items_text = f"{len(invoice.items)} artículos"
                self.table.setItem(row, 2, QTableWidgetItem(items_text))
                
                self.table.setItem(row, 3, QTableWidgetItem(f"${invoice.total:.2f}"))
                self.table.setItem(row, 4, QTableWidgetItem(invoice.estado.value if invoice.estado else ""))
                
                due_date_str = ""
                if invoice.fecha_vencimiento:
                    if isinstance(invoice.fecha_vencimiento, datetime):
                        due_date_str = invoice.fecha_vencimiento.strftime("%Y-%m-%d")
                    else:
                        due_date_str = str(invoice.fecha_vencimiento)
                self.table.setItem(row, 5, QTableWidgetItem(due_date_str))
                
                # Color code by status
                if invoice.estado == InvoiceStatus.PENDING:
                    yellow_color = QColor(Qt.GlobalColor.yellow)
                    light_yellow = yellow_color.lighter(220)
                    for col in range(6):
                        item = self.table.item(row, col)
                        if item:
                            item.setBackground(light_yellow)
            
            # Load account
            account = self.account_controller.get_account(user_id)
            if account:
                self.account_label.setText(
                    f"Saldo Actual: ${account.saldo:.2f} | "
                    f"Total de Movimientos: {len(account.movimientos) if account.movimientos else 0}"
                )
            else:
                self.account_label.setText("No hay información de cuenta disponible")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar facturas: {str(e)}")
            self.table.setRowCount(0)
