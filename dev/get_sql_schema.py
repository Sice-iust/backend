import subprocess
import os

apps_name = ["product",'cart','order','users','wallet','reserve']  
venv_path = r"..\venv"
python_executable = os.path.join(venv_path, "Scripts", "python.exe")
def get_migration_list(app_name):
    result = subprocess.run(
        [python_executable, "..\manage.py", "showmigrations", app_name],
        capture_output=True, text=True
    )
    lines = result.stdout.strip().split("\n")
    migrations = []  
    print(result.stdout)

    for line in lines:
        line = line.strip()
        if line and not line.startswith(app_name):
            parts = line.strip("[X] ").strip("[ ] ").split()
            migrations.append(parts[0])
    print(migrations)
    return migrations

def dump_sql(app_name, migrations, output_file):
    with open(output_file, "w") as f:
        for mig in migrations:
            f.write(f"-- Migration: {mig} --\n")
            result = subprocess.run(
                [python_executable, "..\manage.py", "sqlmigrate", app_name, mig],
                capture_output=True, text=True
            )
            f.write(result.stdout)
            f.write("\n\n")

if __name__ == "__main__":
    for app_name in apps_name:
        output_file = f"{app_name}_schema.sql"
        print(f"Collecting migrations for app: {app_name}")
        migration_list = get_migration_list(app_name)
        print(f"Found migrations: {migration_list}")
        dump_sql(app_name, migration_list, output_file)
        print(f"\nSQL dumped to {output_file}")
