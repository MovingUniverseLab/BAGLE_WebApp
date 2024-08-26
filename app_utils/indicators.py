################################################
# Packages
################################################
import panel as pn


################################################
# Dashboard - Indicators
################################################
ALL_INDICATORS = {
    'startup': pn.pane.GIF('./custom_indicators/startup_indicator/indicator.gif', 
                            name = 'startup_indicator', 
                            width = 190, 
                            margin = (48, 0, 0, 0)),
    'obj_loading': pn.pane.GIF('./custom_indicators/obj_loading_indicator/indicator.gif', 
                                name = 'obj_loading_indicator', 
                                width = 135),
    'error': pn.pane.GIF('./custom_indicators/error_indicator/indicator.gif', 
                            name = 'error_indicator', 
                            width = 160)
    }

# Note: I am putting the GIF panes inside a flexbox because it seems to work better for linux
def get_indicator(name):
    return pn.FlexBox(ALL_INDICATORS[name], styles = {'width':'min-content', 'height':'min-content'})