$(document).ready(function() {
    // Функция форматирования даты
    function formatDateTime(dateString) {
        if (!dateString) return 'Никогда';
        
        const date = new Date(dateString);
        if (isNaN(date.getTime())) return 'Неверная дата';
        
        const day = date.getDate().toString().padStart(2, '0');
        const month = (date.getMonth() + 1).toString().padStart(2, '0');
        const year = date.getFullYear();
        const hours = date.getHours().toString().padStart(2, '0');
        const minutes = date.getMinutes().toString().padStart(2, '0');
        const seconds = date.getSeconds().toString().padStart(2, '0');
        
        return `${day}.${month}.${year}, ${hours}:${minutes}:${seconds}`;
    }

    // Проверка последнего обновления
    function checkLastUpdate() {
        $.get('/api/last_update', function(data) {
            if (data.status === 'success') {
                $('#last-update').text(formatDateTime(data.updated_at));
            } else {
                $('#last-update').text('Ошибка получения данных');
            }
        }).fail(function() {
            $('#last-update').text('Сервер не отвечает');
        });
    }

    // Обновление курсов
    $('#update-rates').click(function() {
        const btn = $(this);
        btn.prop('disabled', true).text('Обновление...');
        
        $.post('/api/update_rates', function(data) {
            if (data.status === 'success') {
                $('#last-update').text(formatDateTime(data.updated_at));
                alert('Курсы успешно обновлены!');
            } else {
                alert('Ошибка: ' + (data.message || 'Не удалось обновить курсы'));
            }
        }).fail(function() {
            alert('Ошибка соединения с сервером');
        }).always(function() {
            btn.prop('disabled', false).text('Обновить курсы');
        });
    });

    // Конвертация валют
    $('#converter-form').submit(function(e) {
        e.preventDefault();
        
        const formData = {
            from: $('#from').val(),
            to: $('#to').val(),
            amount: $('#amount').val()
        };
        
        if (!formData.amount || isNaN(formData.amount) || formData.amount <= 0) {
            alert('Введите корректную сумму');
            return;
        }
        
        const btn = $('.convert-btn');
        btn.prop('disabled', true).text('Конвертация...');
        
        $.ajax({
            url: '/api/convert',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(formData),
            success: function(data) {
                if (data.status === 'success') {
                    $('#result-value').text(`${data.amount} ${data.from} = ${data.result} ${data.to}`);
                    $('#result').show();
                } else {
                    alert('Ошибка: ' + (data.message || 'Не удалось конвертировать'));
                }
            },
            error: function() {
                alert('Ошибка сервера');
            },
            complete: function() {
                btn.prop('disabled', false).text('Конвертировать');
            }
        });
    });

    // Первоначальная проверка
    checkLastUpdate();
});