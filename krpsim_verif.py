from argparse import ArgumentParser, FileType
from tools import StockManager, ProcessInitializer, ErrorManager

class Verification:
    def __init__(self, file, trace):
        self.file = file
        self.trace = trace
        self.stock = dict()
        self.process_list = dict()
        self.optimization_target = str()
        self.initial_stock = dict()
        self.cycle = 0
        self.executed_processes = set()

    def execute(self):
        self.optimization_target = ProcessInitializer.read_process_file(self.file, self.stock, self.process_list)
        self.read_trace()
        self.verify_trace()

    def read_trace(self):
        for line in self.trace:
            cycle, process_name = line.strip().split(':')
            self.cycle = int(cycle)

            if self.cycle < 0:
                ErrorManager.error_verif(self.cycle, '', self.stock, '', 5)

            if process_name != 'no_more_process_doable':
                StockManager.update(self.stock, self.process_list[process_name].result, '+')
                self.executed_processes.add(process_name)
            else:
                break
            self.initial_stock = self.stock.copy()


    def verify_trace(self):
        previous_cycle = -1
        for line in self.trace:
            cycle, process_name = line.strip().split(':')
            self.cycle = int(cycle)
            if self.cycle <= previous_cycle:
                ErrorManager.error_verif(self.cycle, '', self.stock, '', 0)
            previous_cycle = self.cycle
            self.verify_cycle(process_name)

        # Check if all defined processes were executed
        defined_processes = set(self.process_list.keys())
        if defined_processes != self.executed_processes:
            ErrorManager.error_verif(self.cycle, '', self.stock, '', 4)

    def verify_cycle(self, process_name):
        if process_name not in self.process_list:
            ErrorManager.error_verif(self.cycle, process_name, self.stock, '', 2)
        else:
            process = self.process_list[process_name]
            StockManager.update(self.stock, process.need, '+')
            StockManager.update(self.stock, process.result, '-')
            self.check_stock()

            # Check if processes are executed in order
            if process_name not in self.executed_processes:
                ErrorManager.error_verif(self.cycle, process_name, self.stock, '', 3)

    def check_stock(self):
        for key, value in self.stock.items():
            if value < 0:
                ErrorManager.error_verif(self.cycle, '', self.stock, key, 1)

    def display_result(self):
        print(f'\nProgress is correct!\n')
        StockManager.print_stock(self.stock)
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
