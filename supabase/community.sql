-- 자로트립 커뮤니티 (자유게시판 + 불편사항) 설정
-- Supabase 프로젝트 → SQL Editor 에 이 파일 전체를 붙여 넣고 Run.
-- 여러 번 실행해도 안전하다.

create extension if not exists pgcrypto;

-- 1) 자유게시판: 누구나 읽고 쓴다. 글 비밀번호(해시)는 밖으로 내보내지 않는다.
create table if not exists public.posts (
  id bigint generated always as identity primary key,
  nick text not null check (char_length(nick) between 1 and 20),
  body text not null check (char_length(body) between 2 and 2000),
  pw_hash text not null,
  created_at timestamptz not null default now()
);
alter table public.posts enable row level security;
revoke all on public.posts from anon, authenticated;
grant select (id, nick, body, created_at) on public.posts to anon, authenticated;
drop policy if exists "posts readable" on public.posts;
create policy "posts readable" on public.posts for select to anon, authenticated using (true);

-- 글쓰기: 같은 내용 반복·도배를 막고, 비밀번호는 해시로만 저장
create or replace function public.add_post(p_nick text, p_body text, p_pw text)
returns bigint language plpgsql security definer set search_path = public, extensions as $$
declare new_id bigint;
begin
  p_nick := btrim(coalesce(p_nick, '')); p_body := btrim(coalesce(p_body, ''));
  if char_length(p_nick) < 1 or char_length(p_nick) > 20 then raise exception '닉네임은 1~20자'; end if;
  if char_length(p_body) < 2 or char_length(p_body) > 2000 then raise exception '내용은 2~2000자'; end if;
  if char_length(coalesce(p_pw, '')) < 4 then raise exception '비밀번호는 4자 이상'; end if;
  if (select count(*) from posts where created_at > now() - interval '1 minute') >= 10 then
    raise exception '글이 너무 많이 올라오고 있어요. 잠시 뒤에 다시 써 주세요.'; end if;
  if exists (select 1 from posts where body = p_body and created_at > now() - interval '1 day') then
    raise exception '같은 내용의 글이 이미 있어요.'; end if;
  insert into posts (nick, body, pw_hash) values (p_nick, p_body, crypt(p_pw, gen_salt('bf')))
  returning id into new_id;
  return new_id;
end $$;

-- 글 지우기: 쓸 때 정한 비밀번호가 맞을 때만
create or replace function public.delete_post(p_id bigint, p_pw text)
returns boolean language plpgsql security definer set search_path = public, extensions as $$
begin
  delete from posts where id = p_id and pw_hash = crypt(coalesce(p_pw, ''), pw_hash);
  return found;
end $$;

revoke all on function public.add_post(text, text, text) from public;
revoke all on function public.delete_post(bigint, text) from public;
grant execute on function public.add_post(text, text, text) to anon, authenticated;
grant execute on function public.delete_post(bigint, text) to anon, authenticated;

-- 2) 불편사항: 누구나 쓰기만 한다. 읽기 권한은 아무에게도 주지 않는다.
--    운영자는 Supabase 대시보드 → Table Editor → feedback 에서 본다.
create table if not exists public.feedback (
  id bigint generated always as identity primary key,
  category text not null default '기타' check (char_length(category) <= 20),
  body text not null check (char_length(body) between 2 and 3000),
  contact text check (contact is null or char_length(contact) <= 100),
  page text check (page is null or char_length(page) <= 200),
  created_at timestamptz not null default now()
);
alter table public.feedback enable row level security;
revoke all on public.feedback from anon, authenticated;
grant insert (category, body, contact, page) on public.feedback to anon, authenticated;
drop policy if exists "feedback insert only" on public.feedback;
create policy "feedback insert only" on public.feedback for insert to anon, authenticated with check (true);
-- select 정책이 없으므로 사이트 방문자는 불편사항을 읽을 수 없다.
