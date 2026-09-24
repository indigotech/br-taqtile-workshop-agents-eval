INSERT INTO cities (id, name, state, latitude, longitude) VALUES
    (1, 'São Paulo', 'SP', -23.5505, -46.6333),
    (2, 'Rio de Janeiro', 'RJ', -22.9068, -43.1729),
    (3, 'Campos do Jordão', 'SP', -22.7394, -45.5914),
    (4, 'Paraty', 'RJ', -23.2178, -44.7131),
    (5, 'Ubatuba', 'SP', -23.4336, -45.0838),
    (6, 'Belo Horizonte', 'MG', -19.9167, -43.9345),
    (7, 'Ouro Preto', 'MG', -20.3856, -43.5035),
    (8, 'Florianópolis', 'SC', -27.5954, -48.5480);

INSERT INTO users (id, name, email, home_city_id) VALUES
    (1, 'Ana Souza', 'ana@example.com', 1),
    (2, 'Bruno Lima', 'bruno@example.com', 1),
    (3, 'Carla Mendes', 'carla@example.com', 2),
    (4, 'Diego Rocha', 'diego@example.com', 6);

-- Orçamentos variados de propósito: um apertado (Bruno), um folgado (Carla)
-- e dois intermediários, pra que "cabe no orçamento?" tenha respostas diferentes.
INSERT INTO budgets (user_id, total_amount, lodging_amount, food_amount, activities_amount) VALUES
    (1, 1500.00, 700.00, 500.00, 300.00),
    (2, 600.00, 250.00, 250.00, 100.00),
    (3, 4000.00, 2200.00, 1200.00, 600.00),
    (4, 1200.00, 500.00, 450.00, 250.00);

INSERT INTO preferences (user_id, category, value) VALUES
    (1, 'food', 'comida japonesa'),
    (1, 'food', 'cafés'),
    (1, 'activity', 'trilhas'),
    (1, 'lodging', 'airbnb'),
    (2, 'food', 'comida de boteco'),
    (2, 'activity', 'shows de música ao vivo'),
    (2, 'restriction', 'sem carro'),
    (3, 'food', 'frutos do mar'),
    (3, 'activity', 'museus'),
    (3, 'lodging', 'hotel'),
    (3, 'restriction', 'vegetariana'),
    (4, 'food', 'comida mineira'),
    (4, 'activity', 'cidades históricas'),
    (4, 'restriction', 'viaja com cachorro');

INSERT INTO accommodations (id, city_id, kind, name, neighborhood, nightly_price, max_guests, rating) VALUES
    (1, 3, 'hotel', 'Hotel Serra Azul', 'Capivari', 520.00, 2, 4.6),
    (2, 3, 'airbnb', 'Chalé da Mantiqueira', 'Alto do Capivari', 380.00, 4, 4.8),
    (3, 3, 'airbnb', 'Estúdio Vila Inglesa', 'Vila Inglesa', 210.00, 2, 4.3),
    (4, 4, 'hotel', 'Pousada do Porto', 'Centro Histórico', 450.00, 2, 4.7),
    (5, 4, 'airbnb', 'Casa Caiçara', 'Jabaquara', 260.00, 5, 4.5),
    (6, 5, 'hotel', 'Hotel Itaguá', 'Itaguá', 330.00, 3, 4.2),
    (7, 5, 'airbnb', 'Loft Praia Grande', 'Praia Grande', 190.00, 2, 4.4),
    (8, 2, 'hotel', 'Hotel Copacabana Mar', 'Copacabana', 610.00, 2, 4.5),
    (9, 2, 'airbnb', 'Apê Santa Teresa', 'Santa Teresa', 290.00, 3, 4.6),
    (10, 7, 'hotel', 'Pousada Barroca', 'Centro', 340.00, 2, 4.8),
    (11, 7, 'airbnb', 'Casa da Ladeira', 'Antônio Dias', 220.00, 4, 4.4),
    (12, 8, 'hotel', 'Hotel Lagoa', 'Lagoa da Conceição', 480.00, 2, 4.5),
    (13, 8, 'airbnb', 'Casa Campeche', 'Campeche', 310.00, 6, 4.7),
    (14, 1, 'hotel', 'Hotel Paulista', 'Bela Vista', 400.00, 2, 4.1),
    (15, 6, 'airbnb', 'Apê Savassi', 'Savassi', 230.00, 3, 4.3);

INSERT INTO reservations (user_id, accommodation_id, check_in, check_out, guests, total_price, status, created_at) VALUES
    (1, 2, '2026-06-12', '2026-06-14', 2, 760.00, 'confirmed', '2026-05-20 10:15:00'),
    (1, 7, '2026-03-06', '2026-03-08', 1, 380.00, 'cancelled', '2026-02-11 18:40:00'),
    (3, 8, '2026-07-17', '2026-07-19', 2, 1220.00, 'confirmed', '2026-07-01 09:05:00'),
    (4, 10, '2026-04-03', '2026-04-05', 2, 680.00, 'confirmed', '2026-03-15 21:30:00');
