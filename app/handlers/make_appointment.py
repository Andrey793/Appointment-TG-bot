from datetime import datetime
import datetime
from aiogram import  F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery
from aiogram import types
from aiogram.utils.keyboard import ReplyKeyboardBuilder

import database.db_utils as db_utils
import app.keyboards.make_appointment_kb as make_appointment_kb
import app.keyboards.welcome_keyboard as welcome_keyboard
import app.keyboards.registered_users_kb as registered_users_kb



router = Router()

class Make_appointment(StatesGroup) :
    choose_service = State()
    choose_master = State()
    choose_time = State()

@router.callback_query(F.data.startswith('back to main'))
async def cancel_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text='Запись прекращена.')
    await state.clear()

@router.message(F.text.lower() == 'записаться на процедуру')
async def start_appointment(message: Message, state: FSMContext):
    await state.update_data(user=message.from_user.id)
    kb = await make_appointment_kb.get_service()
    await message.answer('Выберете интересующую вас процедуру: ', reply_markup=kb)
    await state.set_state(Make_appointment.choose_service)

@router.callback_query(Make_appointment.choose_service, F.data.startswith('service id: '))
async def choosing_service(callback: CallbackQuery, state: FSMContext):
    service_id = int(callback.data.split(' ')[-1])
    serv = db_utils.get_service_by_id(service_id)
    await state.update_data(service=service_id)
    if (len(db_utils.get_masters_by_service(serv)) == 0) :
        await callback.message.edit_text('К сожалению, пока что, нет мастера, предоставляющего данную услугу(')
        await callback.answer()
        await state.clear()
    else:
        kb = await make_appointment_kb.get_right_masterts(service1=serv)
        await callback.message.edit_text('Выберете мастера предоставляющего данную услугу: ', reply_markup=kb)
        await callback.answer()
        await state.set_state(Make_appointment.choose_master)

@router.callback_query(Make_appointment.choose_master, F.data.startswith('master id: '))
async def choosing_master(callback: CallbackQuery, state: FSMContext):
    appointment_data = await state.get_data()
    service_id = appointment_data['service']
    serv = db_utils.get_service_by_id(service_id=service_id)
    master_id = int(callback.data.split(' ')[-1])
    mast = db_utils.get_master_by_master_id(master_id=master_id)
    await state.update_data(master=master_id)
    if (len(db_utils.get_schedules_by_service_and_master(master=mast, service=serv)) == 0) :
        await callback.message.edit_text('К сожалению у этого мастера нет свободного времени(')
        await callback.answer()
        await state.clear()
    else:
        kb = await make_appointment_kb.get_free_windows(master=mast, service=serv)
        await callback.message.edit_text('Теперь осталось выбрать удобное для вас время: ', reply_markup=kb)
        await callback.answer()
        await state.set_state(Make_appointment.choose_time)

@router.callback_query(Make_appointment.choose_time, F.data.startswith('window: '))
async def choosing_time(callback: CallbackQuery, state: FSMContext):
    time_id = int(callback.data.split(' ')[-1])
    time = db_utils.get_schedule_by_id(time_id)
    await state.update_data(time=time_id)
    appointment_data = await state.get_data()
    master = db_utils.get_master_by_master_id(appointment_data['master'])
    user = db_utils.get_user_by_telegram_id(appointment_data['user'])
    service = db_utils.get_service_by_id(appointment_data['service'])
    schedule = db_utils.get_schedule_by_id(appointment_data['time'])
    db_utils.add_new_appointment(master=master, user=user, service=service, schedule=schedule)
    await callback.message.edit_text(text=f'Запись прошла успешно! \n Вы записаны на процедуру: {service.name} \n К мастеру: {db_utils.get_user_by_master(master).name} \n На: {schedule.start_time} - {schedule.end_time}')
    await state.clear()
    await callback.answer()

@router.callback_query(F.data.startswith('swipe_services:'))
async def swipe_services_page(callback: CallbackQuery, state: FSMContext):
    remover = int(callback.data.split(":")[1])
    kb = await make_appointment_kb.get_service(remover=remover)
    await callback.message.edit_text('Выберете интересующую вас процедуру: ', reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data.startswith('swipe_masters:'))
async def swipe_services_page(callback: CallbackQuery, state: FSMContext):
    appointment_data = await state.get_data()
    service = db_utils.get_service_by_id(appointment_data['service'])
    remover = int(callback.data.split(":")[1])
    kb = await make_appointment_kb.get_right_masterts(service1=service, remover=remover)
    await callback.message.edit_text('Выберете мастера предоставляющего данную услугу: ', reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data.startswith('swipe_time:'))
async def swipe_services_page(callback: CallbackQuery, state: FSMContext):
    appointment_data = await state.get_data()
    service = db_utils.get_service_by_id(appointment_data['service'])
    master = db_utils.get_master_by_master_id(appointment_data['master'])
    remover = int(callback.data.split(":")[1])
    kb = await make_appointment_kb.get_free_windows(master=master, service=service, remover=remover)
    await callback.message.edit_text('Теперь осталось выбрать удобное для вас время: ', reply_markup=kb)
    await callback.answer()