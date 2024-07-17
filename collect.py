import tempfile
import traceback

from config.config import Config
from gui.app import App

def main():
    print('ZZZ 3dmigoto collect script')
    cfg = Config()
    with tempfile.TemporaryDirectory() as temp_dir:
        cfg.temp_data['temp_dir'] = temp_dir
        app = App()
        app.mainloop()
    cfg.save_config()


if __name__ == '__main__':
    try:
        main()
    except SystemExit as X:
        print(X)
        exit()
    except:
        traceback.print_exc()
        input()

