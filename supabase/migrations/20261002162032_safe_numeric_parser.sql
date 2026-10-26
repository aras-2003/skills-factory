create or replace function public.try_numeric(v text)
returns numeric
language plpgsql
immutable
as $$
begin
  if v is null or btrim(v) = '' then return null; end if;
  begin
    return v::numeric;
  exception when others then
    begin
      return substring(v from '[-+]?[0-9]+(?:[.,][0-9]+)?')::numeric;
    exception when others then
      return null;
    end;
  end;
end;
$$;

revoke all on function public.try_numeric(text) from public, anon, authenticated;
grant execute on function public.try_numeric(text) to service_role;
