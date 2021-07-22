from PyQt5.QtWidgets import *
import re
import clans.config as cfg


class FruchtermanReingoldConfig(QDialog):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Configure Fruchterman-Reingold layout")

        self.main_layout = QVBoxLayout()
        self.layout = QGridLayout()

        self.att_val_label = QLabel("Attraction factor")
        self.att_val = QLineEdit(str(cfg.run_params['att_val']))

        self.att_exp_label = QLabel("Attraction exponent (int)")
        self.att_exp = QLineEdit(str(cfg.run_params['att_exp']))

        self.rep_val_label = QLabel("Repulsion factor")
        self.rep_val = QLineEdit(str(cfg.run_params['rep_val']))

        self.rep_exp_label = QLabel("Repulsion exponent (int)")
        self.rep_exp = QLineEdit(str(cfg.run_params['rep_exp']))

        self.gravity_label = QLabel("Gravity")
        self.gravity = QLineEdit(str(cfg.run_params['gravity']))

        self.dampening_label = QLabel("Dampening")
        self.dampening = QLineEdit(str(cfg.run_params['dampening']))

        self.maxmove_label = QLabel("Max. move")
        self.maxmove = QLineEdit(str(cfg.run_params['maxmove']))

        self.cooling_label = QLabel("Cooling")
        self.cooling = QLineEdit(str(cfg.run_params['cooling']))

        self.layout.addWidget(self.att_val_label, 0, 0)
        self.layout.addWidget(self.att_val, 0, 1)

        self.layout.addWidget(self.att_exp_label, 1, 0)
        self.layout.addWidget(self.att_exp, 1, 1)

        self.layout.addWidget(self.rep_val_label, 2, 0)
        self.layout.addWidget(self.rep_val, 2, 1)

        self.layout.addWidget(self.rep_exp_label, 3, 0)
        self.layout.addWidget(self.rep_exp, 3, 1)

        self.layout.addWidget(self.gravity_label, 4, 0)
        self.layout.addWidget(self.gravity, 4, 1)

        self.layout.addWidget(self.dampening_label, 5, 0)
        self.layout.addWidget(self.dampening, 5, 1)

        self.layout.addWidget(self.maxmove_label, 6, 0)
        self.layout.addWidget(self.maxmove, 6, 1)

        self.layout.addWidget(self.cooling_label, 7, 0)
        self.layout.addWidget(self.cooling, 7, 1)

        # Add the OK/Cancel standard buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.main_layout.addLayout(self.layout)
        self.main_layout.addWidget(self.button_box)

        self.setLayout(self.main_layout)

    def get_parameters(self):

        if re.search("^\d+(\.\d+)?$", self.att_val.text()):
            att_val = float(self.att_val.text())
        else:
            att_val = cfg.run_params['att_val']

        if re.search("^\d$", self.att_exp.text()):
            att_exp = int(self.att_exp.text())
        else:
            att_exp = cfg.run_params['att_exp']

        if re.search("^\d+(\.\d+)?$", self.rep_val.text()):
            rep_val = float(self.rep_val.text())
        else:
            rep_val = cfg.run_params['rep_val']

        if re.search("^\d$", self.rep_exp.text()):
            rep_exp = int(self.rep_exp.text())
        else:
            rep_exp = cfg.run_params['rep_exp']

        if re.search("^\d+(\.\d+)?$", self.gravity.text()):
            gravity = float(self.gravity.text())
        else:
            gravity = cfg.run_params['gravity']

        if re.search("^\d+(\.\d+)?$", self.dampening.text()):
            if 0 <= float(self.dampening.text()) <= 1:
                dampening = float(self.dampening.text())
            else:
                dampening = cfg.run_params['dampening']
        else:
            dampening = cfg.run_params['dampening']

        if re.search("^\d+(\.\d+)?$", self.maxmove.text()):
            if float(self.maxmove.text()) > 0:
                maxmove = float(self.maxmove.text())
            else:
                maxmove = cfg.run_params['maxmove']
        else:
            maxmove = cfg.run_params['maxmove']

        if re.search("^\d+(\.\d+)?$", self.cooling.text()):
            if 0 < float(self.cooling.text()) <= 1:
                cooling = float(self.cooling.text())
            else:
                cooling = cfg.run_params['cooling']
        else:
            cooling = cfg.run_params['cooling']

        return att_val, att_exp, rep_val, rep_exp, gravity, dampening, maxmove, cooling



