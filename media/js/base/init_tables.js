function initOrderWorkTable(){
    var grid = $('#order_work_table');
    grid.jqGrid({
        datatype: "local",
        colNames: ["№", "Наименование", "Стоимость за ед.", "Кол-во", "Сумма"],
        colModel: [
            { name:'id', width: 50 },
            { name:'name', editable:true },
            { name:'price', width: 110, editable: true, editrules: {'number': true} },
            { name:'count', width: 60, editable: true, editrules: {'integer': true} },
            { name:'sum', width: 80 }
        ],
        sortname: 'id',
        caption: "Стоимость работ",
        userDataOnFooter: true,
        pager: '#order_work_pager',
        editurl: '/devnull'
    });
    grid.jqGrid('navGrid','#order_work_pager',{});
}

function initOrderMaterialsTable(){
    var grid = $('#order_materials_table');
    grid.jqGrid({
        datatype: "local",
        colNames: ["№", "Наименование", "Номер", "Производитель", "Стоимость за ед.", "Кол-во", "Сумма"],
        colModel: [
            { name:'id', width:50 },
            { name:'name', editable:true },
            { name:'number', width:50, editable:true },
            { name:'manufactorer', editable:true },
            { name:'price', width: 110, editable: true, editrules: {'number': true}},
            { name:'count', width: 60, editable: true, editrules: {'integer': true}},
            { name:'sum', width: 80 }
        ],
        sortname: 'id',
        caption: "Стоимость используемых материалов",
        userDataOnFooter: true,
        pager: '#order_materials_pager',
        editurl: '/devnull'
    });
    grid.jqGrid('navGrid','#order_materials_pager',{});
}

$(function(){
    initOrderWorkTable();
    initOrderMaterialsTable();
});
