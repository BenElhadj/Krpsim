from argparse import ArgumentParser, FileType
from tools import StockManager, ProcessInitializer, ErrorManager

class Verification:
    def __init__(self, file, trace):
        self.file = file
        self.trace = trace
        self.stock = dict()
        self.initial_stock = dict()
        self.process_list = dict()
        self.optimization_target = str()
        self.cycle = 0
        self.max_delay = 0
        self.executed_processes = set()

    def execute(self):
        if not any(self.trace):
            ErrorManager.error_verif(self.cycle, '', self.stock, '', 9)
        self.trace.seek(0)
        self.optimization_target = ProcessInitializer.read_process_file(self.file, self.stock, self.process_list)
        self.initial_stock = self.stock.copy()
        self.read_trace()

    def read_trace(self):
        previous_cycle = 0
        cycle_set = set()
        
        for line in self.trace:
                        
            if not line.strip() or ':' not in line:
                ErrorManager.error_verif(self.cycle, '', self.stock, line.strip(), 10)

            cycle, process_name = line.strip().split(':')
            self.cycle = int(cycle)  

            if process_name not in self.process_list and process_name != 'no_more_process_doable':
                ErrorManager.error_verif(self.cycle, process_name, self.stock, '', 2)
                
            if self.cycle < 0:
                ErrorManager.error_verif(self.cycle, process_name, self.stock, '', 5)
                
            if self.cycle < previous_cycle:
                ErrorManager.error_verif(self.cycle, process_name, self.stock, previous_cycle, 7)

            if process_name != 'no_more_process_doable' and self.executed_processes:
                process = self.process_list[process_name]
                previous_process = self.process_list.get(list(self.executed_processes)[-1], None)
                
                missing_dependencies = [dependency for dependency in process.need if self.stock.get(dependency, 0) < process.need[dependency]]

                if missing_dependencies:
                    additional_info = f'\nDependencies not satisfied for process {process_name}. Needed: {process.need}, Available: {previous_process.result}'
                    ErrorManager.error_verif(self.cycle, process_name, self.stock, additional_info, 8)

                if not any(dependency in previous_process.result for dependency in process.need):
                    pass
                else:
                    if process.delay > 0:
                        delay_cycle = self.cycle - previous_process.start_cycle
                        if self.cycle - previous_cycle != self.max_delay:
                            ErrorManager.error_verif(self.cycle, process_name, self.stock, '', 6)
            else:
                self.max_delay = max(self.max_delay, 1)

            if previous_cycle is not None and self.cycle != previous_cycle:
                self.max_delay = 0

            if process_name != 'no_more_process_doable':
                process = self.process_list[process_name]

                StockManager.update(self.stock, process.need, '-')
                StockManager.update(self.stock, process.result, '+')
                
                self.process_list[process_name].start_cycle = self.cycle
                self.max_delay = max(self.max_delay, self.process_list[process_name].delay)
                self.executed_processes.add(process_name)
            else:
                break
            previous_cycle = self.cycle
            cycle_set.add(self.cycle)
            cycle_set.add(self.cycle)


    def display_result(self):
        print(f'\nProgress is correct!\n')
        
        StockManager.print_stock(self.initial_stock, 'Initial stock:')
        StockManager.print_stock(self.stock, 'Final stock:')
        
        print(f'Last cycle: {self.cycle}\n')

def main():
    parser = ArgumentParser()
    parser.add_argument('file', type=FileType('r'), help='configuration file')
    parser.add_argument('trace', type=FileType('r'), help='trace file')
    args = parser.parse_args()

    verifier = Verification(args.file, args.trace)
    verifier.execute()
    verifier.display_result()

if __name__ == '__main__':
    main()
