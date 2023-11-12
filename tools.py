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
    def print_stock(stock):
        print('Stock:')
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
    def error_verif(cycle, instruction, stock, stock_needed, i):
        error_type = [
            'wrong cycle index for next instruction',
            f"can't execute {instruction}, not enough {stock_needed}",
            f"instruction {instruction} does not exist",
            'out of order process execution',
            'executed processes do not match defined processes',
            'negative cycle value',
            'cycles are not in order',
        ]
        print(f'Error at cycle {cycle}: {error_type[i]}')
        StockManager.print_stock(stock)
        exit(1)
    
    @staticmethod
    def show_error(error_type):
        error_messages = {
            'bad_file': 'Bad file',
            'bad_processes': 'No processes in the folder!!!\nMinimum one process is required'
        }
        print(f'Error: {error_messages[error_type]}')
        exit(1)
        
        
class CustomProcess:
    def __init__(self, line):
        self.name = str()
        self.need = dict()
        self.result = dict()
        self.delay = int()
        self.extract_info(line)

    def extract_info(self, line):
        self.name = line.split(':')[0]

        match_info = re.match(r'\w+:\(([^)]+)\):\(([^)]+)\):(\d+)$', line)
        if match_info:
            need_info, result_info, delay = match_info.groups()

            self.need = {key: int(value) for element in need_info.split(';') for key, value in (element.split(':'),)}
            self.result = {key: int(value) for element in result_info.split(';') for key, value in (element.split(':'),)}
            self.delay = int(delay)
