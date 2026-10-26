create unique index if not exists ux_instruments_isin_nonnull
on public.instruments(isin)
where isin is not null;
