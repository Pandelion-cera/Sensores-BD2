"""
Account widget for viewing account balance and making payments
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QGroupBox,
    QHeaderView, QAbstractItemView, QDialog, QDoubleSpinBox,
    QComboBox, QFormLayout, QDialogButtonBox, QSplitter
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from datetime import datetime

from desktop_app.controllers import get_account_controller
from desktop_app.utils.session_manager import SessionManager
from desktop_app.models.invoice_models import InvoiceStatus, PaymentMethod, PaymentCreate


class PaymentDialog(QDialog):
    """Dialog for making a payment"""
    
    def __init__(self, invoice, parent=None):
        super().__init__(parent)
        self.invoice = invoice
        self.setWindowTitle(f"Pagar Factura #{invoice.id}")
        self.setMinimumWidth(400)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Invoice info
        info_group = QGroupBox("Información de la Factura")
        info_layout = QFormLayout()
        
        info_layout.addRow("ID:", QLabel(str(self.invoice.id)))
        info_layout.addRow("Total:", QLabel(f"${self.invoice.total:.2f}"))
        
        fecha_str = ""
        if self.invoice.fecha_emision:
            if isinstance(self.invoice.fecha_emision, datetime):
                fecha_str = self.invoice.fecha_emision.strftime("%Y-%m-%d")
            else:
                fecha_str = str(self.invoice.fecha_emision)
        info_layout.addRow("Fecha de Emisión:", QLabel(fecha_str))
        
        due_date_str = ""
        if self.invoice.fecha_vencimiento:
            if isinstance(self.invoice.fecha_vencimiento, datetime):
                due_date_str = self.invoice.fecha_vencimiento.strftime("%Y-%m-%d")
            else:
                due_date_str = str(self.invoice.fecha_vencimiento)
        info_layout.addRow("Fecha de Vencimiento:", QLabel(due_date_str))
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Payment form
        form_group = QGroupBox("Datos del Pago")
        form_layout = QFormLayout()
        
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setMinimum(0.01)
        self.amount_spin.setMaximum(999999.99)
        self.amount_spin.setValue(self.invoice.total)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setPrefix("$ ")
        form_layout.addRow("Monto a Pagar:", self.amount_spin)
        
        self.method_combo = QComboBox()
        self.method_combo.addItem("Tarjeta de Crédito", PaymentMethod.CREDIT_CARD)
        self.method_combo.addItem("Tarjeta de Débito", PaymentMethod.DEBIT_CARD)
        self.method_combo.addItem("Transferencia Bancaria", PaymentMethod.BANK_TRANSFER)
        self.method_combo.addItem("Saldo de Cuenta", PaymentMethod.ACCOUNT_BALANCE)
        form_layout.addRow("Método de Pago:", self.method_combo)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def get_payment_data(self):
        """Get payment data from form"""
        return PaymentCreate(
            monto=self.amount_spin.value(),
            metodo=self.method_combo.currentData()
        )


class AccountWidget(QWidget):
    """Widget for viewing account balance and making payments"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.session_manager = SessionManager.get_instance()
        self.account_controller = get_account_controller()
        self.init_ui()
        self.load_account()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Cuenta Corriente")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        # Splitter for two sections
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side: Account balance and movements
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        
        # Account summary
        self.account_group = QGroupBox("Resumen de Cuenta")
        account_layout = QVBoxLayout()
        self.balance_label = QLabel("Cargando...")
        self.balance_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        account_layout.addWidget(self.balance_label)
        
        self.movements_count_label = QLabel("")
        account_layout.addWidget(self.movements_count_label)
        
        # Add balance button
        add_balance_btn = QPushButton("Agregar Saldo")
        add_balance_btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 8px;")
        add_balance_btn.clicked.connect(self.add_balance)
        account_layout.addWidget(add_balance_btn)
        
        account_layout.addStretch()
        self.account_group.setLayout(account_layout)
        left_layout.addWidget(self.account_group)
        
        # Movements table
        movements_label = QLabel("Movimientos de Cuenta")
        movements_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        left_layout.addWidget(movements_label)
        
        self.movements_table = QTableWidget()
        self.movements_table.setColumnCount(5)
        self.movements_table.setHorizontalHeaderLabels([
            "Fecha", "Tipo", "Monto", "Descripción", "Referencia"
        ])
        self.movements_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.movements_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.movements_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        left_layout.addWidget(self.movements_table)
        
        left_widget.setLayout(left_layout)
        splitter.addWidget(left_widget)
        
        # Right side: Pending invoices and payment
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        
        invoices_label = QLabel("Facturas Pendientes")
        invoices_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        right_layout.addWidget(invoices_label)
        
        self.invoices_table = QTableWidget()
        self.invoices_table.setColumnCount(5)
        self.invoices_table.setHorizontalHeaderLabels([
            "ID", "Fecha", "Total", "Vencimiento", "Acción"
        ])
        self.invoices_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.invoices_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.invoices_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        right_layout.addWidget(self.invoices_table)
        
        right_widget.setLayout(right_layout)
        splitter.addWidget(right_widget)
        
        # Set splitter proportions (50% left, 50% right)
        splitter.setSizes([500, 500])
        layout.addWidget(splitter)
        
        # Buttons
        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("Actualizar")
        refresh_btn.clicked.connect(self.load_account)
        btn_layout.addWidget(refresh_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def load_account(self):
        """Load account information and pending invoices"""
        try:
            user_id = self.session_manager.get_user_id()
            if not user_id:
                QMessageBox.warning(self, "Error", "Usuario no conectado")
                return
            
            # Load account
            account = self.account_controller.get_account(user_id)
            
            # Update balance label
            if account:
                balance_color = "#27ae60" if account.saldo >= 0 else "#e74c3c"
                self.balance_label.setText(
                    f"Saldo Actual: <span style='color: {balance_color};'>${account.saldo:.2f}</span>"
                )
                self.balance_label.setTextFormat(Qt.TextFormat.RichText)
                
                self.movements_count_label.setText(
                    f"Total de Movimientos: {len(account.movimientos) if account.movimientos else 0}"
                )
                
                # Load movements
                movements = self.account_controller.list_movements(user_id, skip=0, limit=100)
                self.movements_table.setRowCount(len(movements))
                for row, movement in enumerate(movements):
                    # Date
                    fecha_str = ""
                    if movement.fecha:
                        if isinstance(movement.fecha, datetime):
                            fecha_str = movement.fecha.strftime("%Y-%m-%d %H:%M")
                        else:
                            fecha_str = str(movement.fecha)
                    self.movements_table.setItem(row, 0, QTableWidgetItem(fecha_str))
                    
                    # Type
                    tipo_str = movement.tipo.upper()
                    tipo_item = QTableWidgetItem(tipo_str)
                    if movement.tipo == "cargo":
                        tipo_item.setForeground(QColor("#e74c3c"))  # Red for charges
                    else:
                        tipo_item.setForeground(QColor("#27ae60"))  # Green for payments
                    self.movements_table.setItem(row, 1, tipo_item)
                    
                    # Amount
                    amount_str = f"${movement.monto:.2f}"
                    amount_item = QTableWidgetItem(amount_str)
                    if movement.tipo == "cargo":
                        amount_item.setForeground(QColor("#e74c3c"))
                    else:
                        amount_item.setForeground(QColor("#27ae60"))
                    self.movements_table.setItem(row, 2, amount_item)
                    
                    # Description
                    self.movements_table.setItem(row, 3, QTableWidgetItem(movement.descripcion))
                    
                    # Reference
                    ref_str = movement.referencia_id or ""
                    self.movements_table.setItem(row, 4, QTableWidgetItem(ref_str))
            else:
                self.balance_label.setText("Saldo Actual: $0.00")
                self.movements_count_label.setText("Total de Movimientos: 0")
                self.movements_table.setRowCount(0)
            
            # Load pending invoices
            pending_invoices = self.account_controller.list_pending_invoices(user_id, skip=0, limit=100)
            
            self.invoices_table.setRowCount(len(pending_invoices))
            for row, invoice in enumerate(pending_invoices):
                # ID
                self.invoices_table.setItem(row, 0, QTableWidgetItem(str(invoice.id)))
                
                # Date
                fecha_str = ""
                if invoice.fecha_emision:
                    if isinstance(invoice.fecha_emision, datetime):
                        fecha_str = invoice.fecha_emision.strftime("%Y-%m-%d")
                    else:
                        fecha_str = str(invoice.fecha_emision)
                self.invoices_table.setItem(row, 1, QTableWidgetItem(fecha_str))
                
                # Total
                self.invoices_table.setItem(row, 2, QTableWidgetItem(f"${invoice.total:.2f}"))
                
                # Due date
                due_date_str = ""
                if invoice.fecha_vencimiento:
                    if isinstance(invoice.fecha_vencimiento, datetime):
                        due_date_str = invoice.fecha_vencimiento.strftime("%Y-%m-%d")
                    else:
                        due_date_str = str(invoice.fecha_vencimiento)
                self.invoices_table.setItem(row, 3, QTableWidgetItem(due_date_str))
                
                # Pay button
                pay_btn = QPushButton("Pagar")
                pay_btn.clicked.connect(lambda checked, inv=invoice: self.pay_invoice(inv))
                self.invoices_table.setCellWidget(row, 4, pay_btn)
                
                # Color code overdue invoices
                if invoice.fecha_vencimiento:
                    if isinstance(invoice.fecha_vencimiento, datetime):
                        if invoice.fecha_vencimiento < datetime.utcnow():
                            # Overdue - red background
                            red_color = QColor(Qt.GlobalColor.red)
                            light_red = red_color.lighter(220)
                            for col in range(4):  # Don't color the button column
                                item = self.invoices_table.item(row, col)
                                if item:
                                    item.setBackground(light_red)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar cuenta: {str(e)}")
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error loading account: {e}", exc_info=True)
    
    def pay_invoice(self, invoice):
        """Open payment dialog and process payment"""
        try:
            dialog = PaymentDialog(invoice, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                payment_data = dialog.get_payment_data()
                
                # Initialize services
                # Process payment
                payment = self.account_controller.pay_invoice(invoice.id, payment_data)
                
                QMessageBox.information(
                    self,
                    "Pago Exitoso",
                    f"El pago de ${payment_data.monto:.2f} ha sido registrado exitosamente.\n\n"
                    f"ID de Pago: {payment.id}\n"
                    f"Factura: #{invoice.id}"
                )
                
                # Reload account to show updated balance
                self.load_account()
                
        except ValueError as e:
            QMessageBox.warning(self, "Error de Validación", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al procesar el pago: {str(e)}")
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error processing payment: {e}", exc_info=True)
    
    def add_balance(self):
        """Open dialog to add balance to account"""
        try:
            dialog = AddBalanceDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                amount = dialog.get_amount()
                
                if amount <= 0:
                    QMessageBox.warning(self, "Error", "El monto debe ser mayor a 0")
                    return
                
                user_id = self.session_manager.get_user_id()
                
                # Add balance (abono - increases balance)
                self.account_controller.add_balance(
                    user_id,
                    amount,
                    "Depósito de saldo",
                    None
                )
                
                QMessageBox.information(
                    self,
                    "Saldo Agregado",
                    f"Se han agregado ${amount:.2f} a su cuenta.\n\n"
                    f"Nuevo saldo disponible después de recargar."
                )
                
                # Reload account to show updated balance
                self.load_account()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al agregar saldo: {str(e)}")
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error adding balance: {e}", exc_info=True)


class AddBalanceDialog(QDialog):
    """Dialog for adding balance to account"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Agregar Saldo")
        self.setMinimumWidth(350)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Info label
        info_label = QLabel("Ingrese el monto que desea agregar a su cuenta:")
        layout.addWidget(info_label)
        
        # Amount input
        form_layout = QFormLayout()
        
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setMinimum(0.01)
        self.amount_spin.setMaximum(999999.99)
        self.amount_spin.setValue(0.00)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setPrefix("$ ")
        self.amount_spin.setSingleStep(10.00)
        form_layout.addRow("Monto:", self.amount_spin)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def get_amount(self) -> float:
        """Get amount from form"""
        return self.amount_spin.value()

