$(document).ready(function() {
    //Обработчик нажатия на "Показать подчиненных"
    $(document).on('click', '.toggle-subordinates', function() {
        //Передаем элемент кнопки
        toggleSubordinates($(this));
    });

    //Обработчик нажатия на "Показать подчиненных" внутри подчиненных
    $(document).on('click', '.toggle-subordinate-list', function() {
        //Получаем список подчиненных сотрудников по кнопке
        var subordinateList = $(this).siblings('.subordinate-list');
        //Проверка, загружены ли подчиненные
        if (!subordinateList.data('loaded')) {
            //Если не загружены, загружаем их
            loadSubordinates(subordinateList, $(this).data('employee-id'));
        } else {
            //Если загружены, переключаем видимость списка
            subordinateList.toggle();
        }
    });

    //Функция для переключения видимости списка подчиненных
    function toggleSubordinates(button) {
        //Получаем список подчиненных сотрудников по кнопке
        var subordinateList = button.siblings('.subordinate-list');
        //Проверка, загружены ли подчиненные
        if (!subordinateList.data('loaded')) {
            //Если не загружены, загружаем их
            loadSubordinates(subordinateList, button.data('employee-id'));
        } else {
            //Если загружены, переключаем видимость списка
            subordinateList.toggle();
        }
    }

    //Функция для загрузки подчиненных сотрудников AJAX
    function loadSubordinates(subordinateList, employeeId) {
        //Отправляем AJAX-запрос для получения подчиненных сотрудников
        $.ajax({
            url: '/ajax_subordinates/' + employeeId,
            method: 'GET',
            success: function(response) {
                //Обработка получения подчиненных сотрудников
                response.forEach(function(subordinate) {
                    //Создание элемента списка для каждого подчиненного сотрудника
                    var listItem = $('<li class="list-group-item"></li>');
                    listItem.append('<h6 class="mb-0">' + subordinate.full_name + '</h6>');
                    listItem.append('<p class="mb-0">' + subordinate.position + '</p>');
                    //Если у подчиненного есть еще подчиненные, создаем кнопку для их отображения
                    if (subordinate.has_subordinates) {
                        var toggleButton = $('<button class="btn btn-sm btn-secondary toggle-subordinate-list" data-employee-id="' + subordinate.id + '">Показать подчиненных</button>');
                        var subSubordinateList = $('<ul class="list-group mt-2 subordinate-list" style="display: none;"></ul>');
                        listItem.append(toggleButton);
                        listItem.append(subSubordinateList);
                    }
                    //Добавляние элемента в список подчиненных
                    subordinateList.append(listItem);
                });
                //Пометка списка подчиненных как загруженный и отображение его
                subordinateList.data('loaded', true);
                subordinateList.show();
            },
            //Ошибки AJAX
            error: function(xhr, status, error) {
                console.error(error);
            }
        });
    }
});
