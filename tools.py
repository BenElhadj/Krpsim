import re

class StockManager:
    @staticmethod
    def update(stock, elements, operation='+'):
        for key, value in elements.items():
            if operation == '+':
                stock[key] = stock.get(key, 0) + value
            elif operation == '-':
                stock[key] = stock.get(key, 0) - value
                if stock[key] <= 0:
                    del stock[key]
            else:
                raise ValueError("Invalid operation. Use '+' or '-'.")

    @staticmethod
    def print_stock(stock, msg):
        print(msg)
        for key, value in stock.items():
            print(f' {key} => {value}')
        print('')


class ProcessInitializer:
    @staticmethod
    def initialize_stock(initial_values, stock):
        stock.update({key: stock.get(key, 0) for key in initial_values.keys()})

            
    @staticmethod
    def read_process_file(document, stock, process_list):
        optimization_target = str()
        file_content = document.read()
        file_content = re.sub(r'#.*', '', file_content)

        for line in file_content.split('\n'):
            if line and line != '\n':
                if re.match(r'^\w+:\d+$', line):
                    name, value = line.split(':')
                    stock[name] = int(value)
                elif re.match(r'^\w+:(\((\w+:\d+;?)+\))?:(\((\w+:\d+;?)+\))?:\d+$', line):
                    process = CustomProcess(line)
                    process_list[process.name] = process
                    ProcessInitializer.initialize_stock(process.need, stock)
                    ProcessInitializer.initialize_stock(process.result, stock)
                elif re.match(r'^optimize:\((\w+;?)+\)$', line):
                    optimization_target = re.findall(r'\w+\)$', line)[0][:-1]

        if optimization_target not in stock:
            ErrorManager.show_error('bad_file')

        return optimization_target


class ErrorManager:
    @staticmethod
    def error_verif(cycle, process_name, stock, stock_element, error_type):
        error_messages = {
            0: 'Error: Cycles are not in order.',
            1: f'Error: Stock {stock_element} is negative at cycle {cycle}.',
            2: f'Error: Process {process_name} is not defined.',
            3: f'Error: Process {process_name} does not respect the order of processes.',
            4: f'Error: Process {process_name} has constraints that are not satisfied.',
            5: f'Error: process {process_name} has a negative cycle {cycle}.',
            6: f'Error: Process {process_name} triggered without respecting the daily condition at cycle {cycle}.',
            7: f'Error: Cycles out of order, process {process_name} at cycle {cycle} started after cycle {stock_element}.',
            8: f'Error: Process {process_name} triggered without satisfying all conditions at cycle {cycle}. Additional Info: {stock_element}',
            9: 'Error: The trace file is empty.',
            10: f'Error: Malformed or empty line in the trace file: {stock_element}',
        }

        print(f'\n{error_messages[error_type]}\n')
        StockManager.print_stock(stock, 'Stock:')
        print(f'Last cycle: {cycle}\n')
        exit(1)
    
    @staticmethod
    def error_type(error):
        error_messages = {
            'bad_file': 'Bad file',
            'bad_processes': 'No processes in the folder!!!\nMinimum one process is required'
        }
        print(f'Error: {error_messages[error]}')
        exit(1)
        
        
class CustomProcess:
    def __init__(self, line):
        self.name = str()
        self.need = dict()
        self.result = dict()
        self.delay = int()
        self.extract_info(line)
        self.start_cycle = None

    def extract_info(self, line):
        self.name = line.split(':')[0]

        match_info = re.match(r'\w+:\(([^)]+)\):\(([^)]+)\):(\d+)$', line)
        if match_info:
            need_info, result_info, delay = match_info.groups()

            self.need = {key: int(value) for element in need_info.split(';') for key, value in (element.split(':'),)}
            self.result = {key: int(value) for element in result_info.split(';') for key, value in (element.split(':'),)}
            self.delay = int(delay)
