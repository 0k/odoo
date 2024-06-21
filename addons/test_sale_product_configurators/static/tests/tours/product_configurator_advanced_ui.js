/** @odoo-module **/

import { registry } from "@web/core/registry";
import { stepUtils } from "@web_tour/tour_service/tour_utils";
import configuratorTourUtils from "@test_sale_product_configurators/js/tour_utils";
import { queryFirst } from "@odoo/hoot-dom";

let optionVariantImage;

registry.category("web_tour.tours").add('sale_product_configurator_advanced_tour', {
    url: '/web',
    test: true,
    steps: () => [stepUtils.showAppsMenuItem(), {
    trigger: '.o_app[data-menu-xmlid="sale.sale_menu_root"]',
    run: "click",
},  
{
    trigger: ".o_sale_order",
},
{
    trigger: '.o_list_button_add',
    run: "click",
}, {
    trigger: '.o_required_modifier[name=partner_id] input',
    run: "edit Tajine Saucisse",
}, {
    isActive: ["auto"],
    trigger: '.ui-menu-item > a:contains("Tajine Saucisse")',
    run: "click",
}, 
{
    trigger: ".o_field_widget[name=partner_shipping_id] .o_external_button", // Wait for onchange_partner_id
},
{
    trigger: 'a:contains("Add a product")',
    run: "click",
}, {
    trigger: 'div[name="product_template_id"] input',
    run: "edit Custo",
}, {
    trigger: 'ul.ui-autocomplete a:contains("Customizable Desk (TEST)")',
    run: "click",
},
    ...configuratorTourUtils.selectAndSetCustomAttribute("Customizable Desk", "Legs", "Custom", "Custom 1"),
    ...configuratorTourUtils.selectAndSetCustomAttribute("Customizable Desk", "PA1", "PAV9", "Custom 2"),
    configuratorTourUtils.selectAttribute("Customizable Desk", "PA2", "PAV5"),
    ...configuratorTourUtils.selectAndSetCustomAttribute("Customizable Desk", "PA4", "PAV9", "Custom 3", "select"),
    configuratorTourUtils.assertProductNameContains("Custom, White, PAV9, PAV5, PAV1"),
{
    trigger: 'table.o_sale_product_configurator_table_optional tr:has(td>div[name="o_sale_product_configurator_name"] h5:contains("Conference Chair (TEST) (Steel)"))',
    run: function () {
        const el = queryFirst(
            'table.o_sale_product_configurator_table_optional tr:has(td>div[name="o_sale_product_configurator_name"] h5:contains("Conference Chair (TEST) (Aluminium)")) td[name="o_sale_product_configurator_img"]>img'
        );
        optionVariantImage = el?.getAttribute("src");
    }
},
    configuratorTourUtils.selectAttribute("Conference Chair", "Legs", "Aluminium"),
{
    trigger: 'table.o_sale_product_configurator_table_optional tr:has(td>div[name="o_sale_product_configurator_name"] h5:contains("Conference Chair (TEST) (Aluminium)"))',
    run: function () {
        const el = queryFirst(
            'table.o_sale_product_configurator_table_optional tr:has(td>div[name="o_sale_product_configurator_name"] h5:contains("Conference Chair (TEST) (Aluminium)")) td[name="o_sale_product_configurator_img"]>img'
        );
        let newVariantImage = el?.getAttribute("src");
        if (newVariantImage !== optionVariantImage) {
            console.error('image variant option src changed');
        }
    }
}, {
    trigger: 'button:contains(Confirm)',
    run: "click",
}, {
    trigger: 'td.o_data_cell:contains("Customizable Desk (TEST) (Custom, White, PAV9, PAV5, PAV1)"):not(:contains("PA9: Single PAV"))',
}, {
    trigger: 'td.o_data_cell:contains("Legs: Custom: Custom 1")',
}, {
    trigger: 'td.o_data_cell:contains("PA1: PAV9: Custom 2")',
}, {
    trigger: 'td.o_data_cell:contains("PA4: PAV9: Custom 3")',
}, {
    trigger: 'td.o_data_cell:contains("PA5: PAV1")',
}, {
    trigger: 'td.o_data_cell:contains("PA7: PAV1")',
}, {
    trigger: 'td.o_data_cell:contains("PA8: PAV1")',
}, ...stepUtils.saveForm()
]});
