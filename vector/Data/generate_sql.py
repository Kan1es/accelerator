import csv
import os

CSV_DIR = '/Users/maxkorostelev/accelerator/accelerator/vector/Data/'
OUTPUT_SQL = '/Users/maxkorostelev/accelerator/accelerator/vector/Data/init.sql'

def escape_str(s):
    if s is None:
        return 'NULL'
    return "'" + str(s).replace("'", "''") + "'"

def main():
    tables = [
        {
            'name': 'department',
            'filename': 'department.csv',
            'schema': 'id SERIAL PRIMARY KEY, name VARCHAR(255), parent_id INT REFERENCES department(id)'
        },
        {
            'name': 'role',
            'filename': 'role.csv',
            'schema': 'id SERIAL PRIMARY KEY, name VARCHAR(255), power INT'
        },
        {
            'name': 'employee',
            'filename': 'employees.csv',
            'schema': 'id SERIAL PRIMARY KEY, name VARCHAR(255), role_id INT REFERENCES role(id), department_id INT REFERENCES department(id), is_active BOOLEAN DEFAULT TRUE'
        },
        {
            'name': 'category',
            'filename': 'categories.csv',
            'schema': 'id SERIAL PRIMARY KEY, name VARCHAR(255), keywords TEXT, parent_id INT REFERENCES category(id)'
        },
        {
            'name': 'escalation_rule',
            'filename': 'escalation_rules.csv',
            'schema': 'id SERIAL PRIMARY KEY, category_id INT REFERENCES category(id), time_limit INT'
        },
        {
            'name': 'ticket',
            'filename': 'tickets.csv',
            'schema': 'id SERIAL PRIMARY KEY, description TEXT, category_id INT REFERENCES category(id), priority INT, status VARCHAR(50), created_at TIMESTAMP, creator_id INT REFERENCES employee(id), assignee_id INT REFERENCES employee(id)'
        },
        {
            'name': 'ticket_assignment',
            'filename': 'ticket_assignments.csv',
            'schema': 'id SERIAL PRIMARY KEY, ticket_id INT REFERENCES ticket(id), assignee_id INT REFERENCES employee(id), assigner_id INT REFERENCES employee(id), assigned_time TIMESTAMP, resolved_time TIMESTAMP, is_resolved BOOLEAN DEFAULT FALSE'
        }
    ]
    
    with open(OUTPUT_SQL, 'w', encoding='utf-8') as sql_file:
        for t in tables:
            sql_file.write(f"CREATE TABLE {t['name']} (\n  {t['schema']}\n);\n\n")
            
        for t in tables:
            csv_path = os.path.join(CSV_DIR, t['filename'])
            if not os.path.exists(csv_path):
                continue
            
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    values = []
                    for val in row:
                        if not val:
                            values.append('NULL')
                        elif val in ['t', 'true', 'True']:
                            values.append('TRUE')
                        elif val in ['f', 'false', 'False']:
                            values.append('FALSE')
                        elif val.isdigit():
                            values.append(val)
                        else:
                            # Might be a timestamp or string
                            values.append(escape_str(val))
                    
                    val_str = ', '.join(values)
                    sql_file.write(f"INSERT INTO {t['name']} VALUES ({val_str});\n")
            sql_file.write("\n")
            
    print("Database SQL init script generated successfully at", OUTPUT_SQL)

if __name__ == '__main__':
    main()
