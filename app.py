################################################
# Packages
################################################
import panel as pn
from panel.viewable import Viewer

from app_utils import styles
from app_components import mod_select, paramztn_select, settings_tabs, param_summary, code_panel, plot_panel


################################################
# Initialize Panel
################################################
# Extensions and themes used by panel
pn.extension('tabulator', 'plotly', 'codeeditor', design = styles.THEMES['page_design'])
pn.config.theme = styles.THEMES['page_theme']


################################################
# Dashboard - Layout
################################################
class Dashboard(Viewer):
    def __init__(self, paramztn_info, **params):
        # Note: the order in which the components are instantiated will determine precedence for updates taht have the same dependency

        # Parameter section
        self.paramztn_info = paramztn_info
        self.settings_tabs = settings_tabs.SettingsTabs(paramztn_info = self.paramztn_info)
        super().__init__(**params)
        self.param_summary = param_summary.ParamSummary(paramztn_info = self.paramztn_info, settings_info = self.settings_tabs)
        self.param_row = pn.FlexBox(
            self.param_summary, 
            self.settings_tabs, 
            gap = '0.5%',
            flex_wrap = 'nowrap',
            styles = {'height':'35%'}
        )

        # Code section
        self.code_panel = code_panel.CodePanel(paramztn_info = self.paramztn_info, settings_info = self.settings_tabs)
        
        # Plot section
        self.plot_panel = plot_panel.PlotPanel(paramztn_info = self.paramztn_info, settings_info = self.settings_tabs)

        self.main_row = pn.FlexBox(
            self.plot_panel,
            self.code_panel,
            flex_wrap = 'nowrap',
            gap = '0.5%',
            styles = {'height':'64%', 
                      'width':'100%'}
        )

        # Entire dashboard layout
        self.db_components = self.set_db_components()
        self.dashboard_layout = pn.FlexBox(
            gap = '1%',
            flex_direction = 'column',
            align_content = 'center'
        )


    def set_db_components(self):
        db_components = {}

        # Set labels for plot boxes
        for name in self.plot_panel.plot_names:
            db_components[name] = self.plot_panel.plot_boxes[name]

        # Set label for summary and code display
        db_components['summary'] = self.param_summary.summary_layout
        db_components['code'] = self.code_panel.code_layout

        return db_components
    

    @pn.depends('paramztn_info.selected_paramztn', watch = True)
    def _hide_show(self):
        '''
        Note: Use .clear() and populate the dashboard instead of .visible = True/False. 
              This is because scroll-bar resets and other styling updates for components don't seem to work when .visible = False.
        '''

        if self.paramztn_info.selected_paramztn == None:
            self.dashboard_layout.clear()
            self.dashboard_layout.styles = {}
            
        else:
            # Note: 'set_default_tabs' leads to 'trigger_param_change', which will update everything else (e.g. plots, summary table, etc.)
            # Note: 'selected_paramztn' dependency of set_default_tabs could also be put in settings_tabs.py, 
                # but I chose to put it here to update everything before dashboard gets populated. This is the same with 'set_loading_layout' and 'reset_scroll'.
            self.param_summary.reset_scroll()
            self.code_panel.reset_scroll()
            self.plot_panel.set_loading_layout()
            self.settings_tabs.set_default_tabs()
            self.dashboard_layout.styles = {
                'margin-left':'1%',
                'margin-right':'1%',
                'min-height':'500px',
                'max-height':'1500px',
                'height':'100vh',
                'width': '98%'
            }
            self.dashboard_layout.objects = [self.main_row, self.param_row]


    @pn.depends('settings_tabs.dashboard_checkbox.value', watch = True)
    def _update_layout(self, *event):
        self.plot_panel.set_loading_layout()
        unchecked_components = set(self.db_components.keys()) - set(self.settings_tabs.dashboard_checkbox.value)
        checked_plots = list(set(self.settings_tabs.dashboard_checkbox.value) - {'summary', 'code'})

        for key in self.settings_tabs.dashboard_checkbox.value:
            self.db_components[key].visible = True

        for key in unchecked_components:
            self.db_components[key].visible = False

        # Check for summary
        if 'summary' in self.settings_tabs.dashboard_checkbox.value:
            self.settings_tabs.tabs_layout.tabs_location = 'above'
        else:
             self.settings_tabs.tabs_layout.tabs_location = 'left'

        # Check for number of plots and if code is displayed
        plot_code_bool = [len(checked_plots) > 0, 'code' in self.settings_tabs.dashboard_checkbox.value]
        if True in plot_code_bool:
            match plot_code_bool:
                # At least 1 plot, and code displayed
                case [True, True]:
                    for box in self.plot_panel.plot_boxes.values():
                        box.styles = styles.EXPANDED_PLOTBOX_STYLES

                    # This is a makeshift way to reset the scroll on the plot_layout flexbox
                        # There may be a better way to do this without JS
                    self.plot_panel.plot_layout.append(None)

                # At least 1 plot, and code not displayed
                case [True, False]:
                    # More than 1 plot
                    if len(checked_plots) > 1:
                        for box in self.plot_panel.plot_boxes.values():
                            box.styles = styles.BASE_PLOTBOX_STYLES

                    # Single plot
                    else:
                        self.db_components[checked_plots[0]].styles = styles.EXPANDED_PLOTBOX_STYLES

                # Note: Nothing extra is done if no plots and code is displayed
            
            self.param_row.styles = {'height':'35%'}
            self.main_row.visible = True

            self.plot_panel.plot_layout.visible = plot_code_bool[0]
            self.code_panel.visible = plot_code_bool[1]
            
        # Hide main row and expand param row
        elif 'code' not in self.settings_tabs.dashboard_checkbox.value:
            self.param_row.styles = {'height':'100%'}
            self.main_row.visible = False


    def __panel__(self):
        return self.dashboard_layout
    

################################################
# App Layout
################################################
class BAGLECalc(Viewer):
    def __init__(self, **params):
        self.page_title = pn.widgets.StaticText(
            value = 'BAGLE Calculator', 
            styles = {'font-size': styles.FONTSIZES['page_title'], 
                      'font-weight': '600', 
                      'margin-bottom': '-0.4rem'}
        )
    
        self.mod_row = mod_select.ModSelect()
        self.paramztn_row = paramztn_select.ParamztnSelect(mod_info = self.mod_row)
        self.dashboard = Dashboard(paramztn_info = self.paramztn_row)
    
        # Model header
        self.mod_header = pn.widgets.StaticText(
            value = 'Model:', 
            align = 'end',
            styles = {'font-size': styles.FONTSIZES['page_header'], 
                      'font-weight': '550', 
                      'margin-bottom': '1rem'}
        )
        
        # Parameterization Header
        self.paramztn_header = pn.widgets.StaticText(
            value = f'Parameterization:', 
            align = 'end',
            styles = {'font-size': styles.FONTSIZES['page_header'],
                      'font-weight': '550', 
                      'margin-top': '0'}
        )
    
        self.header_col = pn.Column(
            self.mod_header,
            self.paramztn_header,
            styles = {'margin-top':'-0.08rem'}
        )

        self.selection_col = pn.Column(
            self.mod_row,
            self.paramztn_row,
            styles = {'width':'70%'}
        )

        # Layout for model and parameterization selection rows
        self.selection_layout = pn.FlexBox(
            self.header_col,
            self.selection_col,
            flex_direction = 'row',
            justify_content = 'center',
            flex_wrap = 'nowrap',
            styles = {'width': '90%', 
                      'margin-bottom': '-0.2rem'}
        )
    
        # Content layout for entire page
        self.page_content = pn.FlexBox(
            self.page_title,
            pn.layout.Divider(styles = {'width':'90%'}),
            self.selection_layout,
            pn.layout.Divider(styles = {'width':'90%'}),
            self.dashboard,
            flex_direction = 'column',
            align_items = 'center',
            align_content = 'center',
            styles = {'width': '100%', 
                      'min-width':'1000px',
                      'max-width':'2500px',
                      'height':'fit-content',
                      'overflow':'scroll'}
        )

    def __panel__(self):
        # Center content
        return pn.Row(
            pn.HSpacer(),
            self.page_content,
            pn.HSpacer(),
            styles = {'overflow-y':'hidden', 
                      'overflow-x':'scroll'}
        )
    

################################################
# Server App
################################################
BAGLECalc().servable(title = 'BAGLE Calculator')
