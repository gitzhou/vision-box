# Form implementation generated from reading ui file 'startup.ui'
#
# Created by: PyQt6 UI code generator 6.4.1
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_formStartup(object):
    def setupUi(self, formStartup):
        formStartup.setObjectName("formStartup")
        formStartup.resize(550, 350)
        formStartup.setLocale(QtCore.QLocale(QtCore.QLocale.Language.English, QtCore.QLocale.Country.UnitedStates))
        self.gridLayout = QtWidgets.QGridLayout(formStartup)
        self.gridLayout.setObjectName("gridLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.pushButtonActivate = QtWidgets.QPushButton(parent=formStartup)
        self.pushButtonActivate.setObjectName("pushButtonActivate")
        self.horizontalLayout.addWidget(self.pushButtonActivate)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.pushButtonNew = QtWidgets.QPushButton(parent=formStartup)
        self.pushButtonNew.setObjectName("pushButtonNew")
        self.horizontalLayout.addWidget(self.pushButtonNew)
        self.pushButtonOpen = QtWidgets.QPushButton(parent=formStartup)
        self.pushButtonOpen.setObjectName("pushButtonOpen")
        self.horizontalLayout.addWidget(self.pushButtonOpen)
        self.gridLayout.addLayout(self.horizontalLayout, 1, 0, 1, 1)
        self.plainTextEditWelcome = QtWidgets.QPlainTextEdit(parent=formStartup)
        self.plainTextEditWelcome.setReadOnly(True)
        self.plainTextEditWelcome.setObjectName("plainTextEditWelcome")
        self.gridLayout.addWidget(self.plainTextEditWelcome, 0, 0, 1, 1)

        self.retranslateUi(formStartup)
        QtCore.QMetaObject.connectSlotsByName(formStartup)

    def retranslateUi(self, formStartup):
        _translate = QtCore.QCoreApplication.translate
        formStartup.setWindowTitle(_translate("formStartup", "Startup"))
        self.pushButtonActivate.setText(_translate("formStartup", "Activate"))
        self.pushButtonNew.setText(_translate("formStartup", "Create Account"))
        self.pushButtonOpen.setText(_translate("formStartup", "Open Account"))
