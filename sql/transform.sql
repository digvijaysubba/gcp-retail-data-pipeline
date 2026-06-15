-- Builds the analytics table: daily sales per department.
-- Partitioned by date and clustered by department for efficient querying.

CREATE OR REPLACE TABLE `retail-pipeline-499301.retail.dept_daily_sales`
PARTITION BY order_date
CLUSTER BY department AS
SELECT
  order_date,
  department,
  COUNT(*)                              AS num_line_items,
  SUM(quantity)                         AS total_units,
  ROUND(SUM(quantity * unit_price), 2)  AS total_sales
FROM `retail-pipeline-499301.retail.grocery_orders`
GROUP BY order_date, department;
