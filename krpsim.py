from argparse import ArgumentParser, FileType
from re import findall, match, sub
from ctypes import c_uint
from time import time
from collections import deque
from random import choice, random, randint
from progress.bar import ChargingBar as ProgressBar
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

class MainWalk:
    def __init__(self, initial_stock, optimization_target, process_list, max_cycle, max_instructions):
        self.optimization_target = optimization_target
        self.process_list = process_list
        self.max_instructions = max_instructions
        self.current_stock = initial_stock.copy()
        self.updated_stock = initial_stock.copy()
        self.required_stock = dict()
        self.instruction_dict = dict()
        self.good_instructions = deque()
        self.score = int()
        self.created = int()
        self.loop = True
        self.retrieve_instructions(process_list)
        self.finalize_process(max_cycle)
        self.calculate_score(initial_stock)

    def calculate_score(self, initial_stock):
        self.created = self.updated_stock.get(self.optimization_target, 0)
        
        if not self.good_instructions or self.good_instructions[-1][0] == 0:
            self.score = 0
        else:
            self.score = self.created / self.good_instructions[-1][0]

        if not self.good_instructions or any(self.updated_stock[key] < initial_stock[key] for key in initial_stock) or not self.good_instructions[0][1]:
            self.loop = False

    def finalize_process(self, max_cycle):
        current_cycle = 0
        possible_processes = self.finalize_possible_processes(self.instruction_dict)
        self.good_instructions = [[current_cycle, possible_processes]]
        todo_list = self.update_process_list(current_cycle, possible_processes, {})

        while todo_list and current_cycle <= max_cycle:
            current_cycle = min(map(int, todo_list.keys()))
            for process_name in todo_list[current_cycle]:
                StockManager.update(self.updated_stock, self.process_list[process_name].result, '+')
            del todo_list[current_cycle]
            possible_processes = self.finalize_possible_processes(self.instruction_dict)
            self.good_instructions.append([current_cycle, possible_processes])
            todo_list = self.update_process_list(current_cycle, possible_processes, todo_list)

        return self.good_instructions

    def finalize_possible_processes(self, instruction_dict):
        processes_cycle = []
        
        for key in sorted(instruction_dict.keys(), reverse=True):
            count = instruction_dict[key]
            while count > 0 and self.finalize_process_if_possible(key):
                processes_cycle.append(key)
                instruction_dict[key] -= 1
                count -= 1

        return processes_cycle

    def finalize_process_if_possible(self, process_name):
        temp_stock = self.updated_stock.copy()
        for element, quantity in self.process_list[process_name].need.items():
            if temp_stock[element] < quantity:
                return False
            temp_stock[element] -= quantity
        self.updated_stock = temp_stock
        return True

    def update_process_list(self, current_cycle, actions, todo_list):
        for action in actions:
            todo_list.setdefault(current_cycle + self.process_list[action].delay, []).append(action)
        return todo_list

    def retrieve_instructions(self, process_list):
        self.select_process(self.optimization_target, -1, process_list)
        while self.required_stock:
            required_name = next(iter(self.required_stock))
            if not self.select_process(required_name, self.required_stock[required_name], process_list):
                break

    def select_process(self, required_name, required_quantity, process_list):
        current_stock_required = self.current_stock[required_name]

        if current_stock_required == 0 or required_quantity == -1 or randint(0, 9) >= 9 or self.max_instructions <= 0:
            possible_process_list = self.list_possible_processes(required_name, process_list)

            if not possible_process_list or self.max_instructions <= 0:
                return False

            chosen_process = choice(possible_process_list)
            process_name = chosen_process.name

            self.instruction_dict[process_name] = self.instruction_dict.get(process_name, 0) + 1

            StockManager.update(self.required_stock, chosen_process.need, '+')
            StockManager.update(self.required_stock, chosen_process.result, '-')

            while required_name in self.required_stock and self.max_instructions > 0:
                if self.required_stock[required_name] >= required_quantity:
                    self.max_instructions -= 1
                    break

                self.instruction_dict[process_name] += 1
                StockManager.update(self.required_stock, chosen_process.need, '+')
                StockManager.update(self.required_stock, chosen_process.result, '-')
                self.max_instructions -= 1

        else:
            temp_quantity = current_stock_required - required_quantity
            self.current_stock[required_name] = 0 if temp_quantity < 0 else temp_quantity
            if temp_quantity < 0:
                StockManager.update(self.current_stock, {required_name: temp_quantity}, '-')
            else:
                del self.required_stock[required_name]

        return True

    def list_possible_processes(self, required_name, process_list):
        possible_process_list = list()
        for process in process_list:
            if required_name in process_list[process].result.keys():
                possible_process_list.append(process_list[process])
        return possible_process_list

    def display_process(self):
        print('\nMain walk:')
        process_outputs = {}

        for cycle in self.good_instructions:
            for process_name in cycle[1]:
                if process_name not in process_outputs:
                    process_outputs[process_name] = {'cycles': set(), 'count': 0}
                process_outputs[process_name]['cycles'].add(cycle[0])
                process_outputs[process_name]['count'] += 1

        for process_name, data in process_outputs.items():
            cycles_sorted = sorted(data['cycles'])
            cycles_str = ', '.join(str(cycle) for cycle in cycles_sorted)

            if len(cycles_sorted) > 1:
                cycle_range_str = f'{len(cycles_sorted)} iterations from cycle {cycles_sorted[0]} to cycle {cycles_sorted[-1]}'
                times_per_cycle = data["count"] // len(cycles_sorted)
                times_str = f'({times_per_cycle} times) every {cycles_sorted[1] - cycles_sorted[0]} cycles'
                total_str = f'({data["count"]} times in total)'
                print(f'===> {process_name}: {cycle_range_str}, {times_str} {total_str}')
            else:
                print(f'===> {process_name}: at cycle {cycles_str}: ({data["count"]} times)')

class Simulation:
    def __init__(self, start_time):
        self.max_delay = float()
        self.max_cycle = int()
        self.max_generations = int()
        self.max_instructions = int()
        self.stock = dict()
        self.process_list = dict()
        self.optimization_target = str()
        self.good_instructions = []
        self.start_time = start_time
        self.file_name = str()

    def argument_parser(self):
        parser = ArgumentParser()
        parser.add_argument('file', type=FileType('r'), help='file to optimize')
        parser.add_argument('delay', type=float, help='max time to process')
        parser.add_argument('-c', '--cycle', default=10000, help='max number of cycle. default:10000')
        parser.add_argument('-p', '--process', default=1000, help='max number of process. default:1000')
        parser.add_argument('-i', '--instructions', default=10000,
                            help='max number of instructions allowed during process generation. default:10000')
        args = parser.parse_args()
        self.file_name = args.file.name.rsplit('\\', -2)[-1]
        self.max_cycle = float(args.cycle)
        self.max_delay = args.delay
        self.max_instructions = c_uint(int(args.instructions)).value
        self.max_generations = int(args.process)
        if self.max_generations < 1:
            ErrorManager.show_error('bad_processes')
        self.optimization_target = ProcessInitializer.read_process_file(args.file, self.stock, self.process_list)

    def execute(self):
        delta_time = time() - self.start_time
        progress_bar = ProgressBar('Making process', max=self.max_generations, suffix='%(percent)d%%')
        progress_bar.next()
        main_walk_instance = MainWalk(self.stock, self.optimization_target,
                                     self.process_list, self.max_cycle, self.max_instructions)
        for _ in range(self.max_generations - 1):
            delta_time = time() - self.start_time
            if delta_time > self.max_delay:
                break
            progress_bar.next()
            new_main_walk = MainWalk(self.stock, self.optimization_target,
                                             self.process_list, self.max_cycle, self.max_instructions)
            if new_main_walk.loop > main_walk_instance.loop:
                main_walk_instance = new_main_walk
            elif new_main_walk.loop == main_walk_instance.loop and new_main_walk.score >= main_walk_instance.score:
                if new_main_walk.score == main_walk_instance.score and new_main_walk.created <= main_walk_instance.created:
                    pass
                else:
                    main_walk_instance = new_main_walk
        progress_bar.finish()
        return main_walk_instance

    def display_parsing(self):
        print(
            (f'\nNice file ! {len(self.process_list)} processes, {len(self.stock)} stocks, '
                f'{len([self.optimization_target])} to optimize\n'))

    def display_result(self, main_walk_instance):
        result = str()
        diff_stock = self.stock_difference(main_walk_instance)
        i = 0
        while main_walk_instance.good_instructions[0][1] \
            and main_walk_instance.good_instructions[-1][0] * (i+1) <= self.max_cycle \
                and self.update_stock(diff_stock):
            for cycle in main_walk_instance.good_instructions:
                for element in cycle[1]:
                    result += f'{cycle[0] + main_walk_instance.good_instructions[-1][0]*i}:{element}\n'
            i += 1
            delta_time = time() - self.start_time
            if delta_time > self.max_delay:
                break
        end_time = time() - self.start_time

        file = open(f'{self.file_name}.csv', 'w', encoding='utf-8')
        file.write(result)
        file.close()
        main_walk_instance.display_process()
        print(
            f'\nNo more process doable at cycle {main_walk_instance.good_instructions[-1][0]*i + 1}\n')
        StockManager.print_stock(self.stock)
        print('time:', end_time, )

    def stock_difference(self, main_walk_instance):
        return {key: main_walk_instance.updated_stock[key] - value for key, value in self.stock.items() if main_walk_instance.updated_stock[key] - value}

    def update_stock(self, diff_stock):
        for key, value in diff_stock.items():
            self.stock[key] = max(0, self.stock.get(key, 0) + value)
        return True

def main():
    simulation = Simulation(time())
    simulation.argument_parser()
    simulation.display_parsing()
    main_walk_instance = simulation.execute()
    simulation.display_result(main_walk_instance)
    exit(0)

if __name__ == '__main__':
    main()
