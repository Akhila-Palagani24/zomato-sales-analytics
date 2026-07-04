-- =============================================================
-- Zomato Sales Analytics – SQL Queries
-- Target: SQLite / PostgreSQL / MySQL (minor syntax tweaks noted)
-- Assumes zomato_sales_cleaned.csv loaded into table `orders`
-- =============================================================

-- 0. Table schema (for reference if creating manually)
CREATE TABLE IF NOT EXISTS orders (
    order_id            TEXT PRIMARY KEY,
    order_date          DATE,
    restaurant_name     TEXT,
    city                TEXT,
    region              TEXT,
    food_category       TEXT,
    quantity            INTEGER,
    order_value         NUMERIC,
    discount_pct        NUMERIC,
    delivery_fee        NUMERIC,
    payment_mode        TEXT,
    rating              NUMERIC,
    delivery_time_min   INTEGER,
    is_new_customer     BOOLEAN,
    gross_amount        NUMERIC,
    discount_amount      NUMERIC,
    net_revenue         NUMERIC,
    month               TEXT,
    year                INTEGER,
    weekday             TEXT,
    is_weekend          BOOLEAN
);

-- 1. Top 5 cities by total revenue
SELECT city, ROUND(SUM(net_revenue), 2) AS total_revenue
FROM orders
GROUP BY city
ORDER BY total_revenue DESC
LIMIT 5;

-- 2. Month-over-month revenue growth (window function)
WITH monthly AS (
    SELECT month, SUM(net_revenue) AS revenue
    FROM orders
    GROUP BY month
)
SELECT
    month,
    revenue,
    LAG(revenue) OVER (ORDER BY month) AS prev_month_revenue,
    ROUND(
        (revenue - LAG(revenue) OVER (ORDER BY month)) * 100.0
        / LAG(revenue) OVER (ORDER BY month), 2
    ) AS mom_growth_pct
FROM monthly
ORDER BY month;

-- 3. Category-wise average order value and total revenue
SELECT
    food_category,
    COUNT(*) AS total_orders,
    ROUND(AVG(order_value), 2) AS avg_order_value,
    ROUND(SUM(net_revenue), 2) AS total_revenue
FROM orders
GROUP BY food_category
ORDER BY total_revenue DESC;

-- 4. New vs returning customer revenue split
SELECT
    CASE WHEN is_new_customer = 1 THEN 'New Customer' ELSE 'Returning Customer' END AS customer_type,
    COUNT(*) AS orders,
    ROUND(SUM(net_revenue), 2) AS revenue,
    ROUND(AVG(order_value), 2) AS avg_order_value
FROM orders
GROUP BY is_new_customer;

-- 5. Running total of revenue over time (window function)
SELECT
    order_date,
    net_revenue,
    SUM(net_revenue) OVER (ORDER BY order_date) AS running_total_revenue
FROM orders
ORDER BY order_date;

-- 6. City-wise rank of top-performing food category (window function: RANK)
WITH city_cat AS (
    SELECT city, food_category, SUM(net_revenue) AS revenue
    FROM orders
    GROUP BY city, food_category
)
SELECT city, food_category, revenue, rnk
FROM (
    SELECT *, RANK() OVER (PARTITION BY city ORDER BY revenue DESC) AS rnk
    FROM city_cat
) t
WHERE rnk = 1
ORDER BY revenue DESC;

-- 7. Weekend vs weekday order behavior
SELECT
    is_weekend,
    COUNT(*) AS total_orders,
    ROUND(AVG(order_value), 2) AS avg_order_value,
    ROUND(SUM(net_revenue), 2) AS total_revenue
FROM orders
GROUP BY is_weekend;

-- 8. Impact of discounts on order volume
SELECT
    discount_pct,
    COUNT(*) AS orders,
    ROUND(AVG(order_value), 2) AS avg_order_value
FROM orders
GROUP BY discount_pct
ORDER BY discount_pct;

-- 9. Payment mode preference by region
SELECT region, payment_mode, COUNT(*) AS orders
FROM orders
GROUP BY region, payment_mode
ORDER BY region, orders DESC;

-- 10. Restaurants with rating below 3.5 but high order volume (quality risk flag)
SELECT restaurant_name, city, ROUND(AVG(rating), 2) AS avg_rating, COUNT(*) AS orders
FROM orders
GROUP BY restaurant_name, city
HAVING AVG(rating) < 3.5 AND COUNT(*) > 20
ORDER BY orders DESC;
