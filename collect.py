import tempfile
import traceback

from backend.config.Config import Config
from backend.analysis import targeted_analysis
from backend.utils.texture_utils.TextureManager import TextureManager
from frontend.app import App

def main():
    print('3dmigoto GUI collect script')
    cfg = Config()
    targeted_analysis.clear()
    with tempfile.TemporaryDirectory() as temp_dir:
        cfg.temp_data['temp_dir'] = temp_dir
        app = App()
        TextureManager(temp_dir)
        app.mainloop()
    cfg.save_config()
    targeted_analysis.clear()


if __name__ == '__main__':
    try:
        main()
    except SystemExit as X:
        print(X)
        exit()
    except:
        traceback.print_exc()
        input()

