import csv

class CSVUtil:
    @staticmethod
    def write_csv(f_name, headers: [], col_data:[]):
        with open(f_name, 'a') as f:

            writer = csv.writer(f)
            if len(headers) != 0:
                writer.writerow(headers)
                writer.writerow(col_data)
            else:
                writer.writerow(col_data)    
    
    @staticmethod
    def rm_duplicate(f_name):
        with open(f_name,'r') as in_file, open(f_name + '_pure','w') as out_file:
            seen = set() # set for fast O(1) amortized lookup
            for line in in_file:
                if line in seen: continue # skip duplicate

                seen.add(line)
                out_file.write(line)