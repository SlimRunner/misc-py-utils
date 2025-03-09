import os
import re
import yaml
import datetime
import yfinance as yf
import pandas as pd

from typing import Any
from collections.abc import Iterable, Callable


def main():
    enterMenu = lambda _, enter: enter
    exitOption = lambda name: ("0", CLIMenu(name, lambda stay, enter: None))
    actionFunc = lambda name, func, *params: CLIMenu(
        name, lambda stay, _: func(stay, name, *params)
    )
    mainMenu = CLIMenu("Yahoo Finance", lambda stay, enter: None)

    data = DataWrapper()

    idx = Enum(1, transform=lambda x: str(x))
    queryMenu = CLIMenu("Make query", enterMenu)
    queryMenu.append(idx.count(), actionFunc("input manually", queryYahoo, data))
    queryMenu.append(idx.count(), actionFunc("from file", queryYahoo, data))
    queryMenu.append(*exitOption("back to main"))

    idx.reset()
    visualizeMenu = CLIMenu("visualize", enterMenu)
    visualizeMenu.append(idx.count(), actionFunc("show columns", visData, data))
    visualizeMenu.append(*exitOption("back to main"))

    idx.reset()
    generateMenu = CLIMenu("generate file", enterMenu)
    generateMenu.append(idx.count(), actionFunc("Save to TSV", generateFiles, data))
    generateMenu.append(*exitOption("back to main"))

    idx.reset()
    mainMenu.append(idx.count(), queryMenu)
    mainMenu.append(idx.count(), visualizeMenu)
    mainMenu.append(idx.count(), generateMenu)
    mainMenu.append(*exitOption("exit"))
    mainMenu.run()


class DataWrapper:
    def __init__(self):
        self.payload: Any = None

    def set(self, data):
        self.payload = data


def queryYahoo(status, name, data: DataWrapper):
    match name:
        case "input manually":
            tickers = input("give tickers separated by spaces:\n")
            tickers = re.sub(r" {2,}", " ", tickers)
            dateFrom = input("input date start yyyy-mm-dd:\n")
            dateTo = input("input date end yyyy-mm-dd:\n")
            data.payload = yf.download(
                tickers, start=dateFrom, end=dateTo, auto_adjust=False
            )

        case "from file":
            source = os.path.normpath("./data-in")

            try:
                print()
                filepath = selectFileFromPath(source)
                if filepath is None:
                    print("Operation was canceled")
                else:
                    print("loading", filepath)
                    filepath = os.path.join(source, filepath)
                    with open(filepath, encoding="utf-8") as stream:
                        query = yaml.safe_load(stream)
                        tickers = query["tickers"]
                        dateFrom = query["from"]
                        dateTo = query["to"]
                        if (
                            len(tickers) > 0
                            and isinstance(dateFrom, datetime.date)
                            and isinstance(dateTo, datetime.date)
                        ):
                            data.payload = yf.download(
                                tickers, start=str(dateFrom), end=str(dateTo), auto_adjust=False
                            )
                        else:
                            print(str(dateFrom))
                            print("source file is malformed")
            except yaml.YAMLError as exc:
                print(f"ERROR: {source} could not be loaded")
                print(f"the data was not modified")
            except FileNotFoundError as exc:
                print(*exc.args)

        case "":
            pass

    return status


def visData(status, name, data: DataWrapper):
    if not isinstance(data.payload, pd.DataFrame):
        print("Data is empty")
        return status
    match name:
        case "show columns":
            print(data.payload.columns)

        case "":
            pass

    return status


def generateFiles(status, name, data: DataWrapper):
    if not isinstance(data.payload, pd.DataFrame):
        print("Data is empty")
        return status

    SRC_DIR = "./data-out"

    if not os.path.exists(SRC_DIR):
        os.mkdir(SRC_DIR)

    match name:
        case "Save to TSV":
            monthly_data = data.payload["Adj Close"].resample("ME").mean()
            monthly_return = monthly_data.pct_change().dropna()
            monthly_return.to_csv(os.path.join(SRC_DIR, "montly-returns.tsv"), sep="\t")

            for ticker in monthly_return:
                ret_mean = monthly_return[ticker].mean()
                ret_std = monthly_return[ticker].std()
                print(f"{ticker}: mean {ret_mean}, std {ret_std}")

        case "":
            pass

    return status


def selectFileFromPath(path: str):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Path '{path}' does not exist.")

    files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    if not files:
        raise FileNotFoundError(f"No files found in '{path}'.")

    exitOption = lambda name: ("0", CLIMenu(name, lambda stay, enter: None))
    fileMenu = CLIMenu("Select a file", lambda stay, enter: enter)
    selFile = []
    idx = Enum(1, transform=lambda x: str(x))
    for file in files:
        fileMenu.append(idx.count(), CLIMenu(file, lambda stay, _: selFile.append(file)))

    fileMenu.append(*exitOption("cancel"))
    fileMenu.run()
    return selFile.pop() if selFile else None


class CLIMenu:
    def __init__(self, name: str, action: Callable[[Any, Any], Any]):
        self.__name = name
        self.__items: dict[str, CLIMenu] = dict()
        self.__action = action

    @property
    def name(self):
        return self.__name

    def select(self, parent):
        return self.__action(parent, self)

    def printOptions(self, queue):
        header = [menu.name for menu in queue]
        print(" >> ".join(header))
        for key, item in self.__items.items():
            print(f"    {key}. {item.name}")

    def __readInput(self, msg):
        key = input(msg)
        if key not in self.__items:
            print(f"'{key}' is not a valid option")
            return (None, False)
        return (key, True)

    def append(self, key, item):
        if not isinstance(item, CLIMenu):
            raise ValueError(f"Menu item must of type {type(self).__name__}")
        self.__items[key] = item

    def remove(self, key):
        del self.__items[key]

    def run(self):
        stack = [self]
        while stack:
            root = stack[-1]
            root.printOptions(stack)
            idx, valid = root.__readInput("Choose option: ")
            if not valid:
                continue
            option = root.__items[idx].select(self)
            isMenu = isinstance(option, CLIMenu)
            print()

            if isMenu and option is not self:
                stack.append(option)
            elif not isMenu:
                stack.pop()


class Enum:
    def __init__(self, start: int, step=1, transform=None):
        self.__start = start
        self.reset(start, step)
        self.__transform = (lambda x: x) if transform is None else transform

    def reset(self, start=None, step=1):
        self.__counter = start if isinstance(start, int) else self.__start
        self.__step = step

    def count(self):
        num = self.__counter
        self.__counter += self.__step
        return self.__transform(num)

    def setTransform(self, func: Callable[[int], int]):
        self.__transform = func


if __name__ == "__main__":
    main()
