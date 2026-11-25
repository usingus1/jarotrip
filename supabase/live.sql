-- 자로트립 실시간 접속자 (live.html 의 "지금 접속 중" 숫자)
-- Supabase 프로젝트 → SQL Editor 에 이 파일 전체를 붙여 넣고 Run. 여러 번 실행해도 안전하다.
--
-- 사이트(index.html)가 열려 있는 동안 30초마다 live_ping 을 부른다.
-- 90초 안에 신호를 보낸 방문자를 "지금 접속 중"으로 센다. 개인 정보는 저장하지 않는다
-- (탭마다 새로 만드는 무작위 번호와 보고 있는 화면 이름만 남고, 10분 지나면 지워진다).

create table if not exists public.live_visitors (
  sid text primary key,
  page text,
  seen_at timestamptz not null default now()
);
create index if not exists live_visitors_seen on public.live_visitors (seen_at);
alter table public.live_visitors enable row level security;
revoke all on public.live_visitors from anon, authenticated;
-- 정책이 없으므로 테이블은 직접 읽거나 쓸 수 없고, 아래 두 함수로만 다룬다.

create or replace function public.live_ping(p_sid text, p_page text default null)
returns void language plpgsql security definer set search_path = public as $$
begin
  if p_sid is null or char_length(p_sid) not between 8 and 40 or p_sid !~ '^[A-Za-z0-9_-]+$' then return; end if;
  insert into live_visitors (sid, page, seen_at) values (p_sid, left(coalesce(p_page, 'main'), 30), now())
  on conflict (sid) do update set page = excluded.page, seen_at = now();
  delete from live_visitors where seen_at < now() - interval '10 minutes';
end $$;

-- {"now": 접속 중 인원, "pages": {"plan": 2, "clinics": 1, ...}}
create or replace function public.live_count()
returns json language sql stable security definer set search_path = public as $$
  select json_build_object(
    'now', (select count(*) from live_visitors where seen_at > now() - interval '90 seconds'),
    'pages', coalesce((select json_object_agg(page, n) from (
      select coalesce(page, 'main') as page, count(*) as n from live_visitors
      where seen_at > now() - interval '90 seconds' group by 1) x), '{}'::json)
  );
$$;

revoke all on function public.live_ping(text, text) from public;
revoke all on function public.live_count() from public;
grant execute on function public.live_ping(text, text) to anon, authenticated;
grant execute on function public.live_count() to anon, authenticated;
