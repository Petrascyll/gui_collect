import tempfile
import traceback

from config.config import Config
from targeted_dump import targeted_dump
from gui.app import App

def main():
    print('3dmigoto GUI collect script')
    cfg = Config()
    targeted_dump.clear()
    with tempfile.TemporaryDirectory() as temp_dir:
        cfg.temp_data['temp_dir'] = temp_dir
        app = App()
        app.mainloop()
    cfg.save_config()
    targeted_dump.clear()


if __name__ == '__main__':
    try:
        main()
    except SystemExit as X:
        print(X)
        exit()
    except:
        traceback.print_exc()
        input()

