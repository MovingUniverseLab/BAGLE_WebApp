################################################
# Packages
################################################
import numpy as np

import panel as pn
from panel.viewable import Viewer
import param

from app_utils import constants


################################################
# Model Selection Section
################################################
class ModSelect(Viewer):
    # Dictionary to store selection values
    type_dict = param.Dict(default = {})
    
    def __init__(self, **params):

        # Model selection boxes
        self.srclens_type = pn.widgets.Select(name = '', 
                                        options = {'Point-Source Point-Lens': 'PSPL',
                                                    'Point-Source Binary-Lens': 'PSBL',
                                                    'Binary-Source Point-Lens': 'BSPL',
                                                    'Binary-Source Binary-Lens': 'BSBL'}, 
                                        align = 'center', sizing_mode = 'scale_width', 
                                        stylesheets = [constants.DROPDOWN_STYLE])

        self.data_type = pn.widgets.Select(name = '', 
                                    options = {'Photometry': 'Phot', 
                                                'Astrometry': 'Astrom', 
                                                'Photometry-Astrometry': 'PhotAstrom'}, 
                                    align = 'center', sizing_mode = 'scale_width', 
                                    stylesheets = [constants.DROPDOWN_STYLE])

        self.par_type = pn.widgets.Select(name = '', 
                                    options = {'No Parallax': 'noPar', 
                                                'Parallax': 'Par'}, 
                                    align = 'center', sizing_mode = 'scale_width', 
                                    stylesheets = [constants.DROPDOWN_STYLE])

        self.gp_type = pn.widgets.Select(name = '', 
                                    options = {'No Gaussian Process': '', 
                                                'Gaussian Process': 'GP'}, 
                                    align = 'center', sizing_mode = 'scale_width', 
                                    stylesheets = [constants.DROPDOWN_STYLE])
    
        super().__init__(**params)

        # Initialize type dictionary
        self.update_types()
        
        # Layout of model selection row
        self.mod_layout = self._make_layout()
    
    def _make_layout(self):
        objs = [self.srclens_type, self.data_type, self.par_type, self.gp_type]
        insert_idx = np.arange(1, 2 * len(objs) - 2, 2)
        
        for i in insert_idx:
            plus = pn.widgets.StaticText(name = '', value = '+', align = 'center',
                                         styles = {'font-size':constants.FONTSIZES['plus']})
            objs = np.insert(objs, i, plus) 
            
        
        mod_layout = pn.Row(objects = list(objs), styles = {'margin-bottom':'0.5rem'})
        return mod_layout
    
    @pn.depends('srclens_type.value', 'data_type.value', 'par_type.value', 'gp_type.value', watch = True)
    def update_types(self):
        self.type_dict = {
            'srclens': self.srclens_type.value, 
            'data': self.data_type.value, 
            'par': self.par_type.value, 
            'gp': self.gp_type.value
        }
    
    def __panel__(self):
        return self.mod_layout