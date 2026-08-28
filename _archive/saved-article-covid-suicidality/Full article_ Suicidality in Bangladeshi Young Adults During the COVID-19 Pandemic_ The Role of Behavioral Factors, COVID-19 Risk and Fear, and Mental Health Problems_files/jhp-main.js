$(function (e) {
    var aimsContent = document.querySelector('.aims-content');
    if (aimsContent && aimsContent.scrollHeight <= aimsContent.clientHeight) {
        document.querySelector('.content-wrapper .read-more').hide();
        document.querySelector('.content-wrapper .fade').hide();
    }
});

$(function (e) {
    $('.journalOverviewWidget, .headings-tabs-widget').on('keydown', function (e) {
        if(e.keyCode === 37 || e.keyCode === 39) {
            var tabs = $(this).find(".heading-tabs").children();
            var currentTab = $(e.target);

            if (currentTab.parent().is("li")) {
                currentTab = currentTab.closest("ul");
            }
            if (e.keyCode === 39) {
                if (currentTab.index() === tabs.length - 1) {
                    tabs[0].focus();
                } else {
                    tabs[currentTab.index() + 1].focus();
                }
            }
            if (e.keyCode === 37) {
                if (currentTab.index() === 0) {
                    tabs[tabs.length - 1].focus();
                } else {
                    tabs[currentTab.index() - 1].focus();
                }
            }
        }
    });
});

$(function () {
    var layout = $('.hnm'),
        menu = layout.find('.hnm--menu'),
        compact = $('.compact-nav--dropzone'),
        relocate = menu.data('relocate-search'),
        relocateNav = menu.data('relocate-nav'),
        width = TandfUtils.getClientWidth(),
        relocateWidth = menu.data('relocate-width') || 769;
    if (typeof relocate !== 'undefined' && relocate !== false && width < relocateWidth) {
        $('.sticky-search-bar').attr('data-relocated', 'true');
        layout.find('.hnm--widget').parent().append($("<div/>").addClass("compact-nav").append(compact))
    }

    if (typeof relocateNav !== 'undefined' && relocateNav !== false && width < relocateWidth) {
        layout.parent().prev().before(layout);    
    }

    $('.hnm--search button').on("click", function (e) {
        e.preventDefault();
        $('.hnm--overlay__close').click();
        $(this).attr("aria-label", $(this).attr("aria-label") === "Search" ? "Close search" : "Search");
        $(this).attr("aria-expanded", $(this).attr("aria-expanded") !== "true");
        $(this).find('i.fa').toggleClass('fa-times fa-search')
            .promise()
            .done(function () {
                compact.find('.sticky-search-bar').slideToggle(250);
                $(menu).toggleClass('hnm--searching');
            })
    });
});


