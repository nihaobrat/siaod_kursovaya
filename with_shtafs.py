from tkinter import *
import pandas as pd
import random
from datetime import datetime, timedelta

drivers_A = []  
drivers_B = []  
drivers_shifts = {}

route_types = ['до конечной', 'замкнутый']  
shift_duration_A = 8  
shift_duration_B = 12  
traffic_route_time = 60

start_work_time = '06:00'
end_work_time = '03:00'

def is_weekend(selected_day):
    return selected_day in ['Суббота', 'Воскресенье']

def calculate_route_end(start_time, route_time):
    start_time_obj = datetime.strptime(start_time, "%H:%M")
    end_time_obj = start_time_obj + timedelta(minutes=route_time)
    return end_time_obj.strftime("%H:%M")

def normalize_interval(start_str, end_str):
    start = datetime.strptime(start_str, "%H:%M")
    end = datetime.strptime(end_str, "%H:%M")
    if end < start:
        end += timedelta(days=1)
    return start, end

def is_time_overlap(start_time, end_time, busy_times):
    start, end = normalize_interval(start_time, end_time)
    for busy_start, busy_end in busy_times:
        busy_start_time, busy_end_time = normalize_interval(busy_start, busy_end)
        if start < busy_end_time and end > busy_start_time:
            return True
    return False

def find_intermediate_slots(driver_busy_times, route_time, break_time):
    free_slots = []
    for driver, busy_periods in driver_busy_times.items():
        normalized_periods = []
        for (start, end) in busy_periods:
            start_time, end_time = normalize_interval(start, end)
            normalized_periods.append((start_time, end_time))
        normalized_periods.sort(key=lambda x: x[0])
        current_time = datetime.strptime("06:00", "%H:%M")
        work_end_time = datetime.strptime("03:00", "%H:%M") + timedelta(days=1)
        
        for (st, et) in normalized_periods:
            if (st - current_time).total_seconds()/60 >= route_time + break_time:
                free_slots.append((current_time.strftime("%H:%M"), st.strftime("%H:%M")))
            current_time = et
        if (work_end_time - current_time).total_seconds()/60 >= route_time + break_time:
            free_slots.append((current_time.strftime("%H:%M"), work_end_time.strftime("%H:%M")))
    return free_slots

def calculate_additional_drivers(num_routes, driver_list, shift_duration):
    max_routes_per_driver = int(shift_duration * 60 / traffic_route_time) 
    required_drivers = (num_routes + max_routes_per_driver - 1) // max_routes_per_driver 
    if len(driver_list) >= required_drivers:
        return 0 
    else:
        return required_drivers - len(driver_list)

def print_cannot_generate_message(text_widget, driver_list, shift_duration, num_routes):
    text_widget.delete(1.0, END)
    additional_drivers_needed = calculate_additional_drivers(num_routes, driver_list, shift_duration)
    if additional_drivers_needed > 0:
        text_widget.insert(END, (
            f"Невозможно сгенерировать расписание.\nПопробуйте добавить минимум {additional_drivers_needed} водителей или "
            "уменьшить количество рейсов.\n"
        ))
    else:
        text_widget.insert(END, (
            "Невозможно сгенерировать расписание.\nПопробуйте уменьшить количество рейсов или сократить время маршрута.\n"
        ))

def print_cannot_generate_message_ga(text_widget, driver_list, shift_duration, num_routes):
    text_widget.delete(1.0, END)
    additional_drivers_needed = calculate_additional_drivers(num_routes, driver_list, shift_duration)
    if additional_drivers_needed > 0:
        text_widget.insert(END, (
            f"Генетический алгоритм не смог сгенерировать расписание.\nДобавьте минимум {additional_drivers_needed} водителей или "
            "уменьшите количество рейсов.\n"
        ))
    else:
        text_widget.insert(END, (
            "Генетический алгоритм не смог сгенерировать расписание.\nУменьшите количество рейсов или время маршрута.\n"
        ))

def can_place_route(candidate_start_time, route_time, driver, driver_busy_times, driver_worked_hours, driver_route_counts, min_break_time):
    candidate_end_time = calculate_route_end(candidate_start_time, route_time)
    if is_time_overlap(candidate_start_time, candidate_end_time, driver_busy_times[driver]):
        return False
    if driver_busy_times[driver]:
        last_route_start_str, last_route_end_str = driver_busy_times[driver][-1]
        last_route_end_obj = datetime.strptime(last_route_end_str, "%H:%M")
        last_route_start_obj = datetime.strptime(last_route_start_str, "%H:%M")
        if last_route_end_obj < last_route_start_obj:
            last_route_end_obj += timedelta(days=1)
        candidate_start_time_obj = datetime.strptime(candidate_start_time, "%H:%M")
        if candidate_start_time_obj < last_route_end_obj:
            return False
        if (candidate_start_time_obj - last_route_end_obj).total_seconds()/60 < min_break_time:
            return False
    worked_hours = driver_worked_hours[driver]
    if driver in drivers_A and worked_hours >= shift_duration_A:
        return False
    if driver in drivers_B and worked_hours >= shift_duration_B:
        return False
    candidate_end_time_obj = datetime.strptime(candidate_end_time, "%H:%M")
    if candidate_end_time_obj < datetime.strptime(candidate_start_time, "%H:%M"):
        candidate_end_time_obj += timedelta(days=1)
    end_work_time_obj = datetime.strptime("03:00", "%H:%M") + timedelta(days=1)
    if candidate_end_time_obj > end_work_time_obj:
        return False
    return True

def place_route_any_slot(route_time, break_time, min_break_time, driver_list, driver_busy_times, driver_worked_hours, driver_route_counts,
                          selected_day):
    for attempt in range(50):
        free_slots = find_intermediate_slots(driver_busy_times, route_time, break_time)
        if not free_slots:
            return None
        slot_start, slot_end = random.choice(free_slots)
        slot_start_obj = datetime.strptime(slot_start, "%H:%M")
        slot_end_obj = datetime.strptime(slot_end, "%H:%M")
        if slot_end_obj < slot_start_obj:
            slot_end_obj += timedelta(days=1)
        max_start = (slot_end_obj - slot_start_obj).total_seconds()/60 - route_time
        if max_start < 0:
            continue
        offset = random.randint(0, int(max_start))
        candidate_start_time_obj = slot_start_obj + timedelta(minutes=offset)
        candidate_start_time = candidate_start_time_obj.strftime("%H:%M")
        random.shuffle(driver_list)
        for driver in driver_list:
            if driver in drivers_A and is_weekend(selected_day):
                continue
            if can_place_route(candidate_start_time, route_time, driver, driver_busy_times, driver_worked_hours, driver_route_counts, 
                               min_break_time):
                return (driver, candidate_start_time)
    return None

def generate_optimized_schedule(driver_list, shift_duration, num_routes, selected_day, text_widget, break_time=10, min_break_time=30):
    additional_drivers_needed = calculate_additional_drivers(num_routes, driver_list, shift_duration)
    if additional_drivers_needed > 0:
        text_widget.delete(1.0, END)
        text_widget.insert(END, (
            f"Недостаточно водителей. Добавьте минимум {additional_drivers_needed} водителей или уменьшите число рейсов.\n"
        ))
        return

    schedule = []
    total_routes_assigned = 0
    available_drivers = list(driver_list)
    random.shuffle(available_drivers)
    driver_busy_times = {driver: [] for driver in available_drivers}
    driver_worked_hours = {driver: 0 for driver in available_drivers}
    driver_route_counts = {driver: 0 for driver in available_drivers}
    current_time = datetime.strptime("06:00", "%H:%M")
    end_work_time_obj = datetime.strptime("03:00", "%H:%M") + timedelta(days=1)

    for _ in range(num_routes):
        route_type = random.choice(route_types)
        route_actual_time = traffic_route_time * 2 if route_type == 'замкнутый' else traffic_route_time
        candidate_start_str = current_time.strftime("%H:%M")
        candidate_end_str = calculate_route_end(candidate_start_str, route_actual_time)
        candidate_end_obj = datetime.strptime(candidate_end_str, "%H:%M")
        if candidate_end_obj < current_time:
            candidate_end_obj += timedelta(days=1)
        if candidate_end_obj > end_work_time_obj:
            result = place_route_any_slot(route_actual_time, break_time, min_break_time, available_drivers, driver_busy_times, driver_worked_hours, driver_route_counts, selected_day)
            if result is None:
                print_cannot_generate_message(text_widget, driver_list, shift_duration, num_routes)
                return
            else:
                driver, slot_start = result
                cend = calculate_route_end(slot_start, route_actual_time)
                cend_obj = datetime.strptime(cend, "%H:%M")
                if cend_obj < datetime.strptime(slot_start, "%H:%M"):
                    cend_obj += timedelta(days=1)
                worked_minutes = (cend_obj - datetime.strptime(slot_start, "%H:%M")).seconds / 60
                driver_route_counts[driver] += 1
                final_route_type = route_type + " (доп рейс)"
                schedule.append({
                    'Водитель': driver,
                    'Тип маршрута': final_route_type,
                    'Время начала': slot_start,
                    'Время окончания': cend,
                    'Маршрутов за смену': driver_route_counts[driver]
                })
                driver_busy_times[driver].append((slot_start, cend))
                driver_worked_hours[driver] += worked_minutes / 60
                total_routes_assigned += 1
        else:
            placed = False
            random.shuffle(available_drivers)
            for driver in available_drivers:
                if driver in drivers_A and is_weekend(selected_day):
                    continue
                if can_place_route(candidate_start_str, route_actual_time, driver, driver_busy_times, driver_worked_hours, 
                                   driver_route_counts, min_break_time):
                    cend_obj = candidate_end_obj
                    worked_minutes = (cend_obj - datetime.strptime(candidate_start_str, "%H:%M")).seconds / 60
                    driver_route_counts[driver] += 1
                    schedule.append({
                        'Водитель': driver,
                        'Тип маршрута': route_type,
                        'Время начала': candidate_start_str,
                        'Время окончания': candidate_end_str,
                        'Маршрутов за смену': driver_route_counts[driver]
                    })
                    driver_busy_times[driver].append((candidate_start_str, candidate_end_str))
                    driver_worked_hours[driver] += worked_minutes / 60
                    total_routes_assigned += 1
                    placed = True
                    current_time = cend_obj + timedelta(minutes=break_time + min_break_time)
                    break
            if not placed:
                result = place_route_any_slot(route_actual_time, break_time, min_break_time, available_drivers, driver_busy_times, 
                                              driver_worked_hours, driver_route_counts, selected_day)
                if result is None:
                    print_cannot_generate_message(text_widget, driver_list, shift_duration, num_routes)
                    return
                else:
                    driver, slot_start = result
                    cend = calculate_route_end(slot_start, route_actual_time)
                    cend_obj = datetime.strptime(cend, "%H:%M")
                    if cend_obj < datetime.strptime(slot_start, "%H:%M"):
                        cend_obj += timedelta(days=1)
                    worked_minutes = (cend_obj - datetime.strptime(slot_start, "%H:%M")).seconds / 60
                    driver_route_counts[driver] += 1
                    final_route_type = route_type + " (доп рейс)"
                    schedule.append({
                        'Водитель': driver,
                        'Тип маршрута': final_route_type,
                        'Время начала': slot_start,
                        'Время окончания': cend,
                        'Маршрутов за смену': driver_route_counts[driver]
                    })
                    driver_busy_times[driver].append((slot_start, cend))
                    driver_worked_hours[driver] += worked_minutes / 60
                    total_routes_assigned += 1

    df = pd.DataFrame(schedule)
    text_widget.delete(1.0, END)
    if not df.empty:
        text_widget.insert(END, df.to_string())
    else:
        print_cannot_generate_message(text_widget, driver_list, shift_duration, num_routes)

def try_create_schedule_ga(driver_list, shift_duration, num_routes, selected_day, break_time=10, min_break_time=30):
    available_drivers = list(driver_list)
    random.shuffle(available_drivers)
    driver_busy_times = {driver: [] for driver in available_drivers}
    driver_worked_hours = {driver: 0 for driver in available_drivers}
    driver_route_counts = {driver: 0 for driver in available_drivers}
    schedule = []
    total_routes_assigned = 0

    end_work_time_obj = datetime.strptime("03:00", "%H:%M") + timedelta(days=1)

    def place_in_slot(route_actual_time):
        for attempt in range(50):
            free_slots = find_intermediate_slots(driver_busy_times, route_actual_time, break_time)
            if not free_slots:
                return None
            slot_start, slot_end = random.choice(free_slots)
            slot_start_obj = datetime.strptime(slot_start, "%H:%M")
            slot_end_obj = datetime.strptime(slot_end, "%H:%M")
            if slot_end_obj < slot_start_obj:
                slot_end_obj += timedelta(days=1)
            max_start = (slot_end_obj - slot_start_obj).total_seconds()/60 - route_actual_time
            if max_start < 0:
                continue
            offset = random.randint(0, int(max_start))
            candidate_start_time_obj = slot_start_obj + timedelta(minutes=offset)
            candidate_start_time = candidate_start_time_obj.strftime("%H:%M")
            random.shuffle(available_drivers)
            for driver in available_drivers:
                if driver in drivers_A and is_weekend(selected_day):
                    continue
                if can_place_route(candidate_start_time, route_actual_time, driver, driver_busy_times, driver_worked_hours, 
                                   driver_route_counts, min_break_time):
                    return (driver, candidate_start_time)
        return None

    for i in range(num_routes):
        route_type = random.choice(route_types)
        route_actual_time = traffic_route_time * 2 if route_type == 'замкнутый' else traffic_route_time
        attempts = 0
        placed = False
        while attempts < 50 and not placed:
            attempts += 1
            candidate_start_time = datetime.strptime("06:00", "%H:%M")
            if schedule:
                max_end = datetime.strptime("06:00", "%H:%M")
                for r in schedule:
                    endt = datetime.strptime(r['Время окончания'], "%H:%M")
                    startt = datetime.strptime(r['Время начала'], "%H:%M")
                    if endt < startt:
                        endt += timedelta(days=1)
                    if endt > max_end:
                        max_end = endt
                candidate_start_time = max_end + timedelta(minutes=break_time + min_break_time)
            candidate_start_str = candidate_start_time.strftime("%H:%M")
            candidate_end_str = calculate_route_end(candidate_start_str, route_actual_time)
            candidate_end_obj = datetime.strptime(candidate_end_str, "%H:%M")
            if candidate_end_obj < candidate_start_time:
                candidate_end_obj += timedelta(days=1)
            if candidate_end_obj > end_work_time_obj:
                result = place_in_slot(route_actual_time)
                if result is not None:
                    driver, slot_start = result
                    cend = calculate_route_end(slot_start, route_actual_time)
                    cend_obj = datetime.strptime(cend, "%H:%M")
                    if cend_obj < datetime.strptime(slot_start, "%H:%M"):
                        cend_obj += timedelta(days=1)
                    worked_minutes = (cend_obj - datetime.strptime(slot_start, "%H:%M")).seconds / 60
                    driver_route_counts[driver] += 1
                    final_route_type = route_type + " (доп рейс)"
                    schedule.append({
                        'Водитель': driver,
                        'Тип маршрута': final_route_type,
                        'Время начала': slot_start,
                        'Время окончания': cend,
                        'Маршрутов за смену': driver_route_counts[driver]
                    })
                    driver_busy_times[driver].append((slot_start, cend))
                    driver_worked_hours[driver] += worked_minutes / 60
                    placed = True
                    total_routes_assigned += 1
            else:
                placed_lin = False
                random.shuffle(available_drivers)
                for driver in available_drivers:
                    if driver in drivers_A and is_weekend(selected_day):
                        continue
                    if can_place_route(candidate_start_str, route_actual_time, driver, driver_busy_times, driver_worked_hours, 
                                       driver_route_counts, min_break_time):
                        cend_obj = candidate_end_obj
                        worked_minutes = (cend_obj - datetime.strptime(candidate_start_str, "%H:%M")).seconds / 60
                        driver_route_counts[driver] += 1
                        schedule.append({
                            'Водитель': driver,
                            'Тип маршрута': route_type,
                            'Время начала': candidate_start_str,
                            'Время окончания': candidate_end_str,
                            'Маршрутов за смену': driver_route_counts[driver]
                        })
                        driver_busy_times[driver].append((candidate_start_str, candidate_end_str))
                        driver_worked_hours[driver] += worked_minutes / 60
                        placed = True
                        placed_lin = True
                        # не меняем current_time глобально для ГА
                        break
                if not placed_lin and not placed:
                    result = place_in_slot(route_actual_time)
                    if result is not None:
                        driver, slot_start = result
                        cend = calculate_route_end(slot_start, route_actual_time)
                        cend_obj = datetime.strptime(cend, "%H:%M")
                        if cend_obj < datetime.strptime(slot_start, "%H:%M"):
                            cend_obj += timedelta(days=1)
                        worked_minutes = (cend_obj - datetime.strptime(slot_start, "%H:%M")).seconds / 60
                        driver_route_counts[driver] += 1
                        final_route_type = route_type + " (доп рейс)"
                        schedule.append({
                            'Водитель': driver,
                            'Тип маршрута': final_route_type,
                            'Время начала': slot_start,
                            'Время окончания': cend,
                            'Маршрутов за смену': driver_route_counts[driver]
                        })
                        driver_busy_times[driver].append((slot_start, cend))
                        driver_worked_hours[driver] += worked_minutes / 60
                        placed = True
                        total_routes_assigned += 1
        if not placed:
            break
        else:
            total_routes_assigned += 1

    return schedule, total_routes_assigned

def crossover(schedule1, schedule2):
    half = len(schedule1)//2
    child = schedule1[:half] + schedule2[half:]
    return child

def mutate(schedule):
    if random.random() < 0.1 and len(schedule) > 1:
        i, j = random.sample(range(len(schedule)), 2)
        schedule[i], schedule[j] = schedule[j], schedule[i]
    return schedule

def fitness(schedule, num_routes, drivers_A, drivers_B, traffic_route_time):
    assigned_routes = len(schedule)
    drivers_used = set([route['Водитель'] for route in schedule])
    num_drivers_used = len(drivers_used)
    total_work_minutes = sum([
        (datetime.strptime(route['Время окончания'], "%H:%M") - datetime.strptime(route['Время начала'], "%H:%M")).seconds / 60
        for route in schedule
    ])
    if num_drivers_used > 0:
        average_work_minutes = total_work_minutes / num_drivers_used
    else:
        average_work_minutes = 0
    distribution_penalty = 0
    for driver in drivers_used:
        driver_routes = [route for route in schedule if route['Водитель'] == driver]
        driver_work_minutes = sum([
            (datetime.strptime(route['Время окончания'], "%H:%M") - datetime.strptime(route['Время начала'], "%H:%M")).seconds / 60
            for route in driver_routes
        ])
        distribution_penalty += abs(driver_work_minutes - average_work_minutes)
    weight_routes = 1000
    weight_drivers = 50
    weight_distribution = 10
    fitness_score = (assigned_routes * weight_routes) - (num_drivers_used * weight_drivers) - (distribution_penalty * weight_distribution)
    return fitness_score

def genetic_algorithm_schedule(driver_list, shift_duration, num_routes, selected_day, text_widget, break_time=10, min_break_time=30, 
                               generations=10, population_size=5):
    additional_drivers_needed = calculate_additional_drivers(num_routes, driver_list, shift_duration)
    if additional_drivers_needed > 0:
        text_widget.delete(1.0, END)
        text_widget.insert(END, (
            f"Недостаточно водителей. Нужно добавить минимум {additional_drivers_needed} водителей или "
            "уменьшить число рейсов.\n"
        ))
        return

    population = []
    for _ in range(population_size):
        schedule, score = try_create_schedule_ga(driver_list, shift_duration, num_routes, selected_day, break_time, min_break_time)
        fitness_score = fitness(schedule, num_routes, drivers_A, drivers_B, traffic_route_time)
        population.append((schedule, fitness_score))

    best_schedule = None
    best_score = -float('inf')  
    no_improvement_count = 0
    improvement_limit = 3  

    for gen in range(generations):
        evaluated_population = []
        for individual in population:
            schedule = individual[0]
        
            current_fitness = fitness(schedule, num_routes, drivers_A, drivers_B, traffic_route_time)
            evaluated_population.append((schedule, current_fitness))
        
        evaluated_population.sort(key=lambda x: x[1], reverse=True)
        

        if evaluated_population[0][1] > best_score:
            best_score = evaluated_population[0][1]
            best_schedule = evaluated_population[0][0]
            no_improvement_count = 0
        else:
            no_improvement_count += 1

        if best_score >= num_routes * 1000: 
            break


        if no_improvement_count >= improvement_limit:
            break


        new_population = evaluated_population[:2]  

        while len(new_population) < population_size:
            parent1 = random.choice(evaluated_population)[0]
            parent2 = random.choice(evaluated_population)[0]
            child = crossover(parent1, parent2)
            child = mutate(child)
            child_fitness = fitness(child, num_routes, drivers_A, drivers_B, traffic_route_time)
            new_population.append((child, child_fitness))
        population = new_population


    text_widget.delete(1.0, END)
    if best_schedule and len(best_schedule) > 0:
        df = pd.DataFrame(best_schedule)
        if best_score >= num_routes * 1000:
            text_widget.insert(END, "Генетический алгоритм нашел идеальное решение:\n")
        else:
            text_widget.insert(END, "Генетический алгоритм не нашел идеальное решение, но вот лучший результат:\n")
        text_widget.insert(END, df.to_string())
    else:
        print_cannot_generate_message_ga(text_widget, driver_list, shift_duration, num_routes)

def crossover(schedule1, schedule2):
    half = len(schedule1)//2
    child = schedule1[:half] + schedule2[half:]
    return child

def mutate(schedule):
    if random.random() < 0.1 and len(schedule) > 1:
        i, j = random.sample(range(len(schedule)), 2)
        schedule[i], schedule[j] = schedule[j], schedule[i]
    return schedule

def fitness(schedule, num_routes, drivers_A, drivers_B, traffic_route_time):
    
    assigned_routes = len(schedule)
    

    drivers_used = set([route['Водитель'] for route in schedule])
    num_drivers_used = len(drivers_used)
    

    total_work_minutes = sum([
        (datetime.strptime(route['Время окончания'], "%H:%M") - datetime.strptime(route['Время начала'], "%H:%M")).seconds / 60
        for route in schedule
    ])
    

    if num_drivers_used > 0:
        average_work_minutes = total_work_minutes / num_drivers_used
    else:
        average_work_minutes = 0
    

    distribution_penalty = 0
    for driver in drivers_used:
        driver_routes = [route for route in schedule if route['Водитель'] == driver]
        driver_work_minutes = sum([
            (datetime.strptime(route['Время окончания'], "%H:%M") - datetime.strptime(route['Время начала'], "%H:%M")).seconds / 60
            for route in driver_routes
        ])
        distribution_penalty += abs(driver_work_minutes - average_work_minutes)
    

    weight_routes = 1000
    weight_drivers = 50
    weight_distribution = 10
    

    fitness_score = (assigned_routes * weight_routes) + (num_drivers_used * weight_drivers) - (distribution_penalty * weight_distribution)
    
    return fitness_score

def manage_drivers():
    def delete_driver(driver_name):
        if driver_name in drivers_A:
            drivers_A.remove(driver_name)
        elif driver_name in drivers_B:
            drivers_B.remove(driver_name)
        update_driver_listbox()

    def change_driver_type(driver_name):
        if driver_name in drivers_A:
            drivers_A.remove(driver_name)
            drivers_B.append(driver_name)
        elif driver_name in drivers_B:
            drivers_B.remove(driver_name)
            drivers_A.append(driver_name)
        update_driver_listbox()

    def update_driver_listbox():
        for widget in driver_listbox_frame.winfo_children():
            widget.destroy()
        Label(driver_listbox_frame, text="Водители типа А", bg="#3D0071", fg="white", font=("Helvetica", 12, "bold")).pack(pady=10)
        for driver in drivers_A:
            driver_frame = Frame(driver_listbox_frame, bg="#3D0071")
            driver_frame.pack(fill=X, pady=2)
            Label(driver_frame, text=driver, bg="green", fg="white", width=20, anchor=W).pack(side=LEFT, padx=10)
            Button(driver_frame, text="Удалить", command=lambda d=driver: delete_driver(d), bg="white", fg="#3D0071").pack(side=LEFT, padx=5)
            Button(driver_frame, text="Сменить тип", command=lambda d=driver: change_driver_type(d), bg="white", fg="#3D0071").pack(side=LEFT)
        Label(driver_listbox_frame, text="", bg="#3D0071").pack(pady=5)
        Label(driver_listbox_frame, text="Водители типа Б", bg="#3D0071", fg="white", font=("Helvetica", 12, "bold")).pack(pady=10)
        for driver in drivers_B:
            driver_frame = Frame(driver_listbox_frame, bg="#3D0071")
            driver_frame.pack(fill=X, pady=2)
            Label(driver_frame, text=driver, bg="blue", fg="white", width=20, anchor=W).pack(side=LEFT, padx=10)
            Button(driver_frame, text="Удалить", command=lambda d=driver: delete_driver(d), bg="white", fg="#3D0071").pack(side=LEFT, padx=5)
            Button(driver_frame, text="Сменить тип", command=lambda d=driver: change_driver_type(d), bg="white", fg="#3D0071").pack(side=LEFT)
    manage_window = Toplevel()
    manage_window.title("Управление водителями")
    manage_window.configure(bg="#3D0071")
    Label(manage_window, text="Управление водителями", bg="#3D0071", fg="white", font=("Helvetica", 14, "bold")).pack(pady=10)
    global driver_listbox_frame
    driver_listbox_frame = Frame(manage_window, bg="#3D0071")
    driver_listbox_frame.pack(fill=BOTH, expand=True)
    update_driver_listbox()

def generate_schedule_A():
    try:
        num_routes = int(num_routes_entry.get())
        selected_day = day_choice.get()
        generate_optimized_schedule(drivers_A, shift_duration_A, num_routes, selected_day, schedule_text)
    except ValueError:
        schedule_text.insert(END, "\nОшибка: Введите корректное количество маршруток\n")

def generate_schedule_B():
    try:
        num_routes = int(num_routes_entry.get())
        selected_day = day_choice.get()
        generate_optimized_schedule(drivers_B, shift_duration_B, num_routes, selected_day, schedule_text)
    except ValueError:
        schedule_text.insert(END, "\nОшибка: Введите корректное количество маршруток\n")

def generate_combined_schedule():
    try:
        num_routes = int(num_routes_entry.get())
        combined_drivers = drivers_A + drivers_B
        selected_day = day_choice.get()

        if not drivers_A and not drivers_B:
            schedule_text.insert(END, "\nНет водителей для создания расписания.\n")
            return

        if is_weekend(selected_day) and not drivers_B:
            schedule_text.insert(END, "\nВодители типа А не работают в выходные, а водителей типа Б нет.\n")
            return

        if is_weekend(selected_day) and not drivers_A and drivers_B:
            additional_drivers_needed = calculate_additional_drivers(num_routes, drivers_B, shift_duration_B)
            if additional_drivers_needed > 0:
                schedule_text.insert(END, (
                    f"\nНедостаточно водителей типа Б для выходного дня. Нужно добавить минимум {additional_drivers_needed} водителей.\n"
                ))
                return
            schedule_text.insert(END, (
                "\nВодители типа А не работают в выходные. Создаем расписание только для водителей типа Б.\n"
            ))
            generate_optimized_schedule(drivers_B, shift_duration_B, num_routes, selected_day, schedule_text)
            return

        shift_duration_for_combined = max(shift_duration_A, shift_duration_B)
        generate_optimized_schedule(combined_drivers, shift_duration_for_combined, num_routes, selected_day, schedule_text)
    except ValueError:
        schedule_text.insert(END, "\nОшибка: Введите корректное количество маршруток\n")

def generate_genetic_schedule_A():
    try:
        num_routes = int(num_routes_entry.get())
        selected_day = day_choice.get()

        genetic_algorithm_schedule(drivers_A, shift_duration_A, num_routes, selected_day, schedule_text, generations=50, population_size=20)
    except ValueError:
        schedule_text.insert(END, "\nОшибка: Введите корректное количество маршруток\n")

def generate_genetic_schedule_B():
    try:
        num_routes = int(num_routes_entry.get())
        selected_day = day_choice.get()

        genetic_algorithm_schedule(drivers_B, shift_duration_B, num_routes, selected_day, schedule_text, generations=50, population_size=20)
    except ValueError:
        schedule_text.insert(END, "\nОшибка: Введите корректное количество маршруток\n")

def generate_genetic_schedule_AB():
    try:
        num_routes = int(num_routes_entry.get())
        combined_drivers = drivers_A + drivers_B
        selected_day = day_choice.get()

        if not drivers_A and not drivers_B:
            schedule_text.insert(END, "\nНет водителей для создания расписания.\n")
            return

        if is_weekend(selected_day) and not drivers_B:
            schedule_text.insert(END, "\nВодители типа А не работают в выходные, а водителей типа Б нет.\n")
            return

        if is_weekend(selected_day) and not drivers_A and drivers_B:
            additional_drivers_needed = calculate_additional_drivers(num_routes, drivers_B, shift_duration_B)
            if additional_drivers_needed > 0:
                schedule_text.insert(END, (
                    f"\nНедостаточно водителей типа Б для выходного дня. Нужно добавить минимум {additional_drivers_needed} водителей.\n"
                ))
                return
            schedule_text.insert(END, (
                "\nВодители типа А не работают в выходные. Создаем генетическое расписание только для водителей типа Б.\n"
            ))
            genetic_algorithm_schedule(drivers_B, shift_duration_B, num_routes, selected_day, schedule_text, generations=50, population_size=20)
            return

        shift_duration_for_combined = max(shift_duration_A, shift_duration_B)
        genetic_algorithm_schedule(combined_drivers, shift_duration_for_combined, num_routes, selected_day, schedule_text, generations=50, 
        population_size=20)
    except ValueError:
        schedule_text.insert(END, "\nОшибка: Введите корректное количество маршруток\n")

def new_function_placeholder():
    pass

def reset_all():
    num_routes_entry.delete(0, END)
    route_time_entry.delete(0, END)
    schedule_text.delete(1.0, END)
    print("\nСброс всех данных выполнен.\n")

def set_route_time():
    global traffic_route_time
    try:
        traffic_route_time = int(route_time_entry.get())
        schedule_text.insert(END, "\nВремя маршрута успешно установлено.\n")
    except ValueError:
        schedule_text.insert(END, "\nОшибка: Введите корректное время маршрута в минутах.\n")

def run_gui():
    global num_routes_entry, route_time_entry, schedule_text, traffic_route_time, day_choice
    root = Tk()
    root.title("Регистрация водителей и расписание маршруток")
    root.geometry("1900x1080")

    main_frame = Frame(root)
    main_frame.pack(fill="both", expand=True)

    form_frame = Frame(main_frame, bg="#3D0071")
    form_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
    form_frame.grid_columnconfigure(0, weight=1)

    button_frame = Frame(main_frame, bg="#3D0071")
    button_frame.pack(side="right", fill="y", padx=10, pady=10)

    Label(form_frame, text="Регистрация водителей", bg="#3D0071", fg="white", font=("Helvetica", 14, "bold")).grid(row=0, column=0, pady=10)

    Label(form_frame, text="Введите фамилию водителя:", bg="#3D0071", fg="white").grid(row=1, column=0, pady=5)
    driver_name_entry = Entry(form_frame, font=("Helvetica", 12), relief="solid", bd=2)
    driver_name_entry.grid(row=2, column=0, pady=5)

    driver_type = StringVar(root)
    driver_type.set("A")

    driver_menu = OptionMenu(form_frame, driver_type, "A", "B")
    driver_menu.config(font=("Helvetica", 12), relief="solid", bd=2)
    driver_menu.grid(row=3, column=0, pady=5)

    def register_driver():
        driver_name = driver_name_entry.get().strip()
        driver_choice = driver_type.get()
        if not driver_name:
            status_label.config(text="Ошибка: Имя водителя не может быть пустым", fg="red")
            return
        if driver_choice == "A":
            drivers_A.append(driver_name)
        else:
            drivers_B.append(driver_name)
        driver_name_entry.delete(0, END)
        status_label.config(text=f"Водитель {driver_name} добавлен как тип {driver_choice}", fg="white")

    status_label = Label(form_frame, text="", bg="#3D0071", fg="white", font=("Helvetica", 12))
    status_label.grid(row=4, column=0, pady=5)

    Label(form_frame, text="Выберите день недели:", bg="#3D0071", fg="white", font=("Helvetica", 12)).grid(row=5, column=0, pady=5)
    day_choice = StringVar(root)
    day_choice.set("Понедельник")
    days_menu = OptionMenu(form_frame, day_choice, "Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье")
    days_menu.config(font=("Helvetica", 12), relief="solid", bd=2)
    days_menu.grid(row=6, column=0, pady=5)

    Label(form_frame, text="Введите количество рейсов на день:", bg="#3D0071", fg="white", font=("Helvetica", 12)).grid(row=7, column=0, pady=5)
    num_routes_entry = Entry(form_frame, font=("Helvetica", 12), relief="solid", bd=2)
    num_routes_entry.grid(row=8, column=0, pady=5)

    Label(form_frame, text="Введите время маршрута в минутах:", bg="#3D0071", fg="white", font=("Helvetica", 12)).grid(row=9, column=0, pady=5)
    route_time_entry = Entry(form_frame, font=("Helvetica", 12), relief="solid", bd=2)
    route_time_entry.grid(row=10, column=0, pady=5)

    schedule_text = Text(form_frame, height=20, width=90, bg="white", fg="black", font=("Courier", 10), relief="solid", bd=2, wrap=WORD)
    schedule_text.grid(row=11, column=0, pady=10)

    register_button = Button(button_frame, text="Добавить водителя", command=register_driver, bg="white", fg="#3D0071", font=("Helvetica", 12), relief="solid", bd=2)
    register_button.pack(pady=5, fill="x")

    set_time_button = Button(button_frame, text="Установить время маршрута", command=set_route_time, bg="white", fg="#3D0071", font=("Helvetica", 12), relief="solid", bd=2)
    set_time_button.pack(pady=5, fill="x")

    generate_button_A = Button(button_frame, text="Сгенерировать расписание из водителей типа А", command=generate_schedule_A, bg="white", fg="#3D0071", font=("Helvetica", 12), relief="solid", bd=2)
    generate_button_A.pack(pady=5, fill="x")

    generate_button_B = Button(button_frame, text="Сгенерировать расписание из водителей типа Б", command=generate_schedule_B, bg="white", fg="#3D0071", font=("Helvetica", 12), relief="solid", bd=2)
    generate_button_B.pack(pady=5, fill="x")

    generate_button_combined = Button(button_frame, text="Сгенерировать совместное расписание", command=generate_combined_schedule, bg="white", fg="#3D0071", font=("Helvetica", 12), relief="solid", bd=2)
    generate_button_combined.pack(pady=5, fill="x")

    genetic_button_A = Button(button_frame, text="Генетическое расписание для типа А", command=generate_genetic_schedule_A, bg="white", fg="#3D0071", font=("Helvetica", 12), relief="solid", bd=2)
    genetic_button_A.pack(pady=5, fill="x")

    genetic_button_B = Button(button_frame, text="Генетическое расписание для типа Б", command=generate_genetic_schedule_B, bg="white", fg="#3D0071", font=("Helvetica", 12), relief="solid", bd=2)
    genetic_button_B.pack(pady=5, fill="x")

    genetic_button_AB = Button(button_frame, text="Генетическое расписание для типа А и Б", command=generate_genetic_schedule_AB, bg="white", fg="#3D0071", font=("Helvetica", 12), relief="solid", bd=2)
    genetic_button_AB.pack(pady=5, fill="x")

    manage_button = Button(button_frame, text="Управление водителями", command=manage_drivers, bg="white", fg="#3D0071", font=("Helvetica", 12), relief="solid", bd=2)
    manage_button.pack(pady=5, fill="x")

    reset_button = Button(button_frame, text="Сброс", command=reset_all, bg="red", fg="white", font=("Helvetica", 12), relief="solid", bd=2)
    reset_button.pack(pady=10, fill="x")

    root.mainloop()

run_gui()
