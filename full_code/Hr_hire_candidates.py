from Hr_resume_status import mark_as_hired, load_status

def main():
    resume_filename = input("Enter resume filename to mark as hired: ").strip()

    status_data = load_status()

    if resume_filename in status_data and status_data[resume_filename]["status"] == "hired":
        print(f"{resume_filename} is already marked as hired.")
        return

    mark_as_hired(resume_filename)
    print(f"{resume_filename} successfully marked as hired.")

if __name__ == "__main__":
    main()
