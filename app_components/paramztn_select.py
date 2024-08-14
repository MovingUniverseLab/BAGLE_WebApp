################################################
# Packages
################################################
import re
from functools import partial

from bagle import model

import panel as pn
from panel.viewable import Viewer
from bokeh.models import Tooltip
from bokeh.models.dom import HTML
import param

from app_utils import constants, styles
from app_components import mod_select
    

################################################
# Parameterization Selection Section
################################################
class ParamztnSelect(Viewer):
    # To be instantiated class (required input)
    mod_info = param.ClassSelector(class_ = mod_select.ModSelect)
    
    # Current selected paramertization and parameters
    selected_paramztn = param.String(allow_None = True)
    selected_params = param.List()
    selected_phot_params = param.List()
    
    # Dictionary to store buttons
    paramztn_btns = param.Dict(default = {})
    

    def __init__(self, **params):
        # Flex box to display buttons
        self.paramztn_box = pn.FlexBox(align = 'center')

        # Error message in case of no parameterizations
        self.paramztn_error = pn.pane.HTML(
            object = f'''
                <div style="font-size:{styles.FONTSIZES['error_paramztn']};font-family:{styles.HTML_FONTFAMILY}">
                    <span><b>ERROR:</b> There are currently no supported parameterizations for this model.</span>
                    </br>
                    <span>Please try a different selection.</span>
                </div>
            ''',
            styles = {'color':styles.CLRS['error_primary'], 
                      'margin-bottom': '0', 
                      'text-align':'center', 
                      'width':'100%'}
        )
        
        # Layout of parameterization selection row
        self.paramztn_layout = pn.Row()

        super().__init__(**params)


    @pn.depends('mod_info.type_dict', watch = True, on_init = True)
    def update_paramztn(self):
        '''
        Updates the contents of the parameterization selection row of the page.
        '''  
        mod_types = self.mod_info.type_dict
        
        # Clear selected parameterization
        self.selected_paramztn = None
        
        # Get paramaterizations for selected model   
        if mod_types['gp'] == '':
            mod_regex = '_'.join([mod_types[key] for key in mod_types.keys() 
                                  if key != 'gp']) + '_Param'
        elif mod_types['gp'] == 'GP':
            mod_regex = '_'.join(list(mod_types.values())) + '_Param'

        mod_paramztns = [mod for mod in constants.ALL_MODS if re.match(mod_regex, mod)]
            
        # No parameterizations found for selected model
        if len(mod_paramztns) == 0:
            self.paramztn_layout.objects = [pn.HSpacer(), self.paramztn_error, pn.HSpacer()]
            
        # Parameterizations found for selected model
        else:
            for paramztn in mod_paramztns:
                # Check if button exists
                if paramztn in self.paramztn_btns.keys():
                    # Reset style of existing button
                    self.paramztn_btns[paramztn].stylesheets = [styles.BASE_BTN_STYLESHEET]

                else:
                    # Write HTML for button tooltip
                    all_param_names = self.get_param_names(paramztn, mod_types)

                    tooltip_html = ''.join([f'''<span>{param}</span>''' for param in all_param_names])
                    tooltip_html = HTML(f'''
                        <div style = "display:flex; align-items:center; flex-direction:column; 
                                      padding:0.25rem; border:0.04rem black solid; color:{styles.CLRS['page_primary']};
                                      font-size:{styles.FONTSIZES['tooltip']}; font-weight:bold;">
                            {tooltip_html}
                        </div>
                    ''')

                    # Create parameterization button
                    self.paramztn_btns[paramztn] = pn.widgets.Button(
                        name = paramztn, button_type = 'primary', 
                        description = (Tooltip(content = tooltip_html, position = 'bottom')),
                        stylesheets = [styles.BASE_BTN_STYLESHEET]
                    )

                # Add/Update on-click action for button
                self.paramztn_btns[paramztn].on_click(partial(self._change_selected_btn, mod_types = mod_types))

            # Get relevant buttons and update paramztn_box
            self.paramztn_box.objects = [self.paramztn_btns[key] for key in mod_paramztns]
            self.paramztn_layout.objects = [self.paramztn_box]


    def get_param_names(self, paramztn, mod_types, return_phot_names = False):
        # Get paramaterization class
        class_num = re.search('Param.*', paramztn).group()
        if mod_types['gp'] == 'GP':
            param_class_str = '_'.join([mod_types['srclens'], 'GP', mod_types['data'] + class_num])
        else:
            param_class_str = '_'.join([mod_types['srclens'], mod_types['data'] + class_num])

        param_class = getattr(model, param_class_str)
        
        # Get required parameters for paramaterization
        all_param_names = (param_class.fitter_param_names + param_class.phot_param_names + 
                           param_class.phot_optional_param_names + param_class.ast_optional_param_names)
        
        if mod_types['par'] == 'Par':
            all_param_names += ['raL', 'decL']
        
        # Check if phot_names should be returned
        if return_phot_names == True:
            return param_class.phot_param_names, all_param_names
        else:
            return all_param_names
    

    def _change_selected_btn(self, event, mod_types): 
        if (event.obj.name != self.selected_paramztn):

            # Change CSS of new selected button
            event.obj.stylesheets = [styles.SELECTED_BTN_STYLESHEET]

            # Reset CSS of old selected button if it exists
            if self.selected_paramztn != None:
                self.paramztn_btns[self.selected_paramztn].stylesheets = [styles.BASE_BTN_STYLESHEET]

            # Update selected parameters and parameterization
                # Note: the selected parameters needs to be updated first
            self.selected_phot_params, self.selected_params = self.get_param_names(event.obj.name, mod_types, return_phot_names = True)
            self.selected_paramztn = event.obj.name


    def __panel__(self):
        return self.paramztn_layout