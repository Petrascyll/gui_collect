import traceback
import gui_collect


if __name__ == '__main__':
    try:
        gui_collect.main()
    except SystemExit as X:
        print(X)
        exit()
    except:
        traceback.print_exc()
        input()

