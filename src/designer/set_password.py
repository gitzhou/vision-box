# Form implementation generated from reading ui file 'set_password.ui'
#
# Created by: PyQt6 UI code generator 6.4.1
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_dialogSetPassword(object):
    def setupUi(self, dialogSetPassword):
        dialogSetPassword.setObjectName("dialogSetPassword")
        dialogSetPassword.resize(500, 180)
        dialogSetPassword.setLocale(QtCore.QLocale(QtCore.QLocale.Language.English, QtCore.QLocale.Country.UnitedStates))
        self.gridLayout = QtWidgets.QGridLayout(dialogSetPassword)
        self.gridLayout.setObjectName("gridLayout")
        self.labelDescription = QtWidgets.QLabel(parent=dialogSetPassword)
        self.labelDescription.setObjectName("labelDescription")
        self.gridLayout.addWidget(self.labelDescription, 0, 0, 1, 1)
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setFieldGrowthPolicy(QtWidgets.QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        self.formLayout.setContentsMargins(-1, 10, -1, 10)
        self.formLayout.setObjectName("formLayout")
        self.labelPassword = QtWidgets.QLabel(parent=dialogSetPassword)
        self.labelPassword.setObjectName("labelPassword")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.ItemRole.LabelRole, self.labelPassword)
        self.lineEditPassword = QtWidgets.QLineEdit(parent=dialogSetPassword)
        self.lineEditPassword.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.lineEditPassword.setObjectName("lineEditPassword")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.ItemRole.FieldRole, self.lineEditPassword)
        self.labelConfirm = QtWidgets.QLabel(parent=dialogSetPassword)
        self.labelConfirm.setObjectName("labelConfirm")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.ItemRole.LabelRole, self.labelConfirm)
        self.lineEditConfirm = QtWidgets.QLineEdit(parent=dialogSetPassword)
        self.lineEditConfirm.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.lineEditConfirm.setObjectName("lineEditConfirm")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.ItemRole.FieldRole, self.lineEditConfirm)
        self.gridLayout.addLayout(self.formLayout, 1, 0, 1, 1)
        self.buttonBox = QtWidgets.QDialogButtonBox(parent=dialogSetPassword)
        self.buttonBox.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.StandardButton.Cancel|QtWidgets.QDialogButtonBox.StandardButton.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 2, 0, 1, 1)

        self.retranslateUi(dialogSetPassword)
        self.buttonBox.accepted.connect(dialogSetPassword.accept) # type: ignore
        self.buttonBox.rejected.connect(dialogSetPassword.reject) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(dialogSetPassword)

    def retranslateUi(self, dialogSetPassword):
        _translate = QtCore.QCoreApplication.translate
        dialogSetPassword.setWindowTitle(_translate("dialogSetPassword", "Set Password"))
        self.labelDescription.setText(_translate("dialogSetPassword", "Set a password to encrypt account files."))
        self.labelPassword.setText(_translate("dialogSetPassword", "Password :"))
        self.labelConfirm.setText(_translate("dialogSetPassword", "Confirm :"))
