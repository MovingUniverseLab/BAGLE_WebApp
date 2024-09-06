################################################
# Packages
################################################
import panel as pn
import os


################################################
# Dashboard - Indicators
################################################
FILE_PATH = os.path.dirname(__file__)
ALL_LOGOS = {
    'mulab': pn.pane.PNG(
        object = FILE_PATH + '/../logos/mulab_logo.png',
        alt_text = 'MU Lab',
        link_url = 'https://jluastro.atlassian.net/wiki/spaces/MULab/overview',
        height = 70,
        styles = {'margin':'0'}
    ),
        
    'github': pn.pane.PNG(
        object = FILE_PATH + '/../logos/github-mark-white.png',
        alt_text = 'GitHub Repo',
        link_url = 'https://github.com/MovingUniverseLab/BAGLE_WebApp',
        height = 55,
        styles = {'margin':'0'}
    )
}