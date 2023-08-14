import json
import random
from .models import *
from account.forms import *
from account.models import *
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.serializers.json import DjangoJSONEncoder


# 메인페이지
def main(request):
    polls = Poll.objects.all()
    sort = request.GET.get("sort")
    promotion_polls = Poll.objects.filter(active=True).order_by("-pub_date")[:3]
    if sort == "popular":
        polls = polls.order_by("-views_count")  # 인기순
    elif sort == "latest":
        polls = polls.order_by("-id")  # 최신순
    elif sort == "oldest":
        polls = polls.order_by("id")  # 등록순

    page = request.GET.get("page")
    random_poll = random.choice(polls) if polls else None
    paginator = Paginator(polls, 4)
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page = 1
        page_obj = paginator.page(page)
    except EmptyPage:
        page = paginator.num_pages
        page_obj = paginator.page(page)
    context = {
        "polls": polls,
        "page_obj": page_obj,
        "paginator": paginator,
        "promotion_polls": promotion_polls,
        "random_poll": random_poll,
    }

    return render(request, "vote/main.html", context)


# 투표 디테일 페이지
def poll_detail(request, poll_id):
    user = request.user
    poll = get_object_or_404(Poll, id=poll_id)

    if user.is_authenticated and user.voted_polls.filter(id=poll_id).exists():
        calcstat_url = reverse("vote:calcstat", args=[poll_id])
        return redirect(calcstat_url)
    else:
        poll.increase_views()  # 게시글 조회 수 증가
        loop_count = poll.choice_set.count()
        context = {
            "poll": poll,
            "loop_time": range(0, loop_count),
        }
        response = render(request, "vote/detail.html", context)
        return response


# 투표 게시글 좋아요 초기 검사
def get_like_status(request, poll_id):
    try:
        poll = Poll.objects.get(id=poll_id)
    except Poll.DoesNotExist:
        return JsonResponse({"error": "해당 투표가 존재하지 않습니다."}, status=404)

    user = request.user
    user_likes_poll = False

    if request.user.is_authenticated:
        if poll.poll_like.filter(id=user.id).exists():
            user_likes_poll = True

    context = {"user_likes_poll": user_likes_poll}
    return JsonResponse(context)


# 투표 게시글 좋아요
@login_required
def poll_like(request):
    if request.method == "POST":
        req = json.loads(request.body)
        poll_id = req["poll_id"]

        try:
            poll = Poll.objects.get(id=poll_id)
        except Poll.DoesNotExist:
            return JsonResponse({"error": "해당 투표가 존재하지 않습니다."}, status=404)

        user = request.user
        if request.user.is_authenticated:
            if poll.poll_like.filter(id=user.id).exists():
                poll.poll_like.remove(user)
                message = "좋아요 취소"
                user_likes_poll = False
            else:
                poll.poll_like.add(user)
                message = "좋아요"
                user_likes_poll = True

            like_count = poll.poll_like.count()
            context = {
                "like_count": like_count,
                "message": message,
                "user_likes_poll": user_likes_poll,
            }
            return JsonResponse(context)
        return redirect("/")


# 유저 마이페이지
@login_required(login_url="/account/login/")  # 비로그인시 /mypage 막음
def mypage(request):
    polls = Poll.objects.all()
    page = request.GET.get("page")

    paginator = Paginator(polls, 4)
    uservotes = UserVote.objects.filter(user=request.user)
    polls_like = Poll.objects.filter(poll_like=request.user)

    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page = 1
        page_obj = paginator.page(page)
    except EmptyPage:
        page = paginator.num_pages
        page_obj = paginator.page(page)
    context = {
        "polls": polls,
        "uservotes": uservotes,
        "polls_like": polls_like,
        "page_obj": page_obj,
        "paginator": paginator,
    }
    return render(request, "vote/mypage.html", context)


# 마이페이지 정보 수정
@login_required(login_url="/account/login/")  # 비로그인시 mypage/update 막음
def mypage_update(request):
    if request.method == "POST":
        form = UserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect("vote:mypage")
    else:
        form = UserChangeForm(instance=request.user)
    context = {"form": form}
    return render(request, "vote/update.html", context)


# 댓글 쓰기
@login_required
def comment_write_view(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id)
    user_info = request.user  # 현재 로그인한 사용자
    content = request.POST.get("content")
    parent_comment_id = request.POST.get("parent_comment_id")
    if content:
        if parent_comment_id:  # 대댓글인 경우
            parent_comment = get_object_or_404(Comment, pk=parent_comment_id)
            comment = Comment.objects.create(
                poll=poll,
                content=content,
                user_info=user_info,
                parent_comment=parent_comment,
            )

            parent_comment_data = {
                "nickname": parent_comment.user_info.nickname,
                "mbti": parent_comment.user_info.mbti,
                "gender": parent_comment.user_info.gender,
                "content": parent_comment.content,
                "created_at": parent_comment.created_at.strftime("%Y년 %m월 %d일"),
                "comment_id": parent_comment.pk,
            }
        else:  # 일반 댓글인 경우
            comment = Comment.objects.create(
                poll=poll,
                content=content,
                user_info=user_info,
            )
            parent_comment_data = None

        poll.update_comments_count()  # 댓글 수 업데이트
        poll.save()

        try:
            user_vote = UserVote.objects.get(
                user=request.user, poll=poll
            )  # uservote에서 선택지 불러옴
            choice_text = user_vote.choice.choice_text
        except UserVote.DoesNotExist:
            user_vote = None
            choice_text = ""  # 또는 다른 기본값 설정

        comment_id = comment.pk

        data = {
            "nickname": user_info.nickname,
            "mbti": user_info.mbti,
            "gender": user_info.gender,
            "content": content,
            "created_at": comment.created_at.strftime("%Y년 %m월 %d일"),
            "comment_id": comment_id,
            "choice": choice_text,
        }
        if parent_comment_data:
            data["parent_comment"] = parent_comment_data

        return HttpResponse(
            json.dumps(data, cls=DjangoJSONEncoder), content_type="application/json"
        )


# 댓글 삭제
@login_required
def comment_delete_view(request, pk):
    poll = get_object_or_404(Poll, id=pk)
    comment_id = request.POST.get("comment_id")
    target_comment = Comment.objects.get(pk=comment_id)

    if request.user == target_comment.user_info:
        target_comment.delete()
        poll.save()
        data = {"comment_id": comment_id, "success": True}
    else:
        data = {"success": False, "error": "본인 댓글이 아닙니다."}
    return HttpResponse(
        json.dumps(data, cls=DjangoJSONEncoder), content_type="application/json"
    )


# 대댓글 수 파악
def calculate_nested_count(request, comment_id):
    nested_count = Comment.objects.filter(parent_comment_id=comment_id).count()
    return JsonResponse({"nested_count": nested_count})


# 투표 시 회원, 비회원 구분 (비회원일시 성별 기입)
def classifyuser(request, poll_id):
    if request.method == "POST":
        poll = get_object_or_404(Poll, pk=poll_id)
        choice_id = request.POST.get("choice")  # 뷰에서 선택 불러옴
        user = request.user
        if choice_id:
            choice = Choice.objects.get(id=choice_id)
            try:
                vote = UserVote(user=request.user, poll=poll, choice=choice)
                vote.save()
                user.voted_polls.add(poll_id)
                calcstat_url = reverse("vote:calcstat", args=[poll_id])
                voted_polls = user.voted_polls.all()
                return redirect(calcstat_url)
            except ValueError:
                vote = NonUserVote(poll=poll, choice=choice)
                vote.save()
                nonuservote_id = vote.id
                poll = get_object_or_404(Poll, pk=poll_id)
                context = {
                    "poll": poll,
                    "gender": ["M", "W"],
                    "nonuservote_id": nonuservote_id,
                    "loop_time": range(0, 2),
                }
                return render(request, "vote/detail2.html", context)
    else:
        return redirect("/")


# 회원/비회원 투표 통계 계산 및 결과 페이지
def calcstat(request, poll_id):
    poll = get_object_or_404(Poll, pk=poll_id)
    comments = Comment.objects.filter(poll_id=poll_id)
    if request.user.is_authenticated:
        user_votes = UserVote.objects.filter(user=request.user)
    else:
        user_votes = None  # 또는 user_votes = UserVote.objects.none()

    mbtis = [
        "ISTJ",
        "ISFJ",
        "INFJ",
        "INTJ",
        "ISTP",
        "ISFP",
        "INFP",
        "INTP",
        "ESTP",
        "ESFP",
        "ENFP",
        "ENTP",
        "ESTJ",
        "ESFJ",
        "ENFJ",
        "ENTJ",
    ]

    user_poll = UserVote.objects.filter(choice__poll__pk=poll_id)
    user_total_count = user_poll.count()

    user_choice1 = user_poll.filter(choice_id=2 * poll_id - 1)
    user_choice1_count = user_choice1.count()

    user_choice2 = user_poll.filter(choice_id=2 * poll_id)
    user_choice2_count = user_choice2.count()

    user_man = UserVote.objects.filter(choice__poll__pk=poll_id, user__gender="M")
    user_man_count = user_man.count()

    user_man_choice1 = user_man.filter(choice_id=2 * poll_id - 1)
    user_man_choice1_count = user_man_choice1.count()

    user_man_choice2 = user_man.filter(choice_id=2 * poll_id)
    user_man_choice2_count = user_man_choice2.count()

    user_woman = UserVote.objects.filter(choice__poll__pk=poll_id, user__gender="W")
    user_woman_count = user_woman.count()

    user_woman_choice1 = user_woman.filter(choice_id=2 * poll_id - 1)
    user_woman_choice1_count = user_woman_choice1.count()

    user_woman_choice2 = user_woman.filter(choice_id=2 * poll_id)
    user_woman_choice2_count = user_woman_choice2.count()

    user_mbtis_count = []
    user_mbtis_choice1_count = []
    user_mbtis_choice2_count = []

    for mbti in mbtis:
        user_mbti = UserVote.objects.filter(choice__poll__pk=poll_id, user__mbti=mbti)
        user_mbti_count = user_mbti.count()
        user_mbtis_count.append(user_mbti_count)

        user_mbti_choice1 = user_mbti.filter(choice_id=2 * poll_id - 1)
        user_mbti_choice1_count = user_mbti_choice1.count()
        user_mbtis_choice1_count.append(user_mbti_choice1_count)

        user_mbti_choice2 = user_mbti.filter(choice_id=2 * poll_id)
        user_mbti_choice2_count = user_mbti_choice2.count()
        user_mbtis_choice2_count.append(user_mbti_choice2_count)

    nonuser_poll = NonUserVote.objects.filter(
        choice__poll__pk=poll_id, MBTI__isnull=False, gender__isnull=False
    )

    nonuser_total_count = nonuser_poll.count()

    nonuser_choice1 = nonuser_poll.filter(choice_id=2 * poll_id - 1)
    nonuser_choice1_count = nonuser_choice1.count()

    nonuser_choice2 = nonuser_poll.filter(choice_id=2 * poll_id)
    nonuser_choice2_count = nonuser_choice2.count()

    nonuser_man = NonUserVote.objects.filter(choice__poll__pk=poll_id, gender="M")
    nonuser_man_count = nonuser_man.count()

    nonuser_man_choice1 = nonuser_man.filter(choice_id=2 * poll_id - 1)
    nonuser_man_choice1_count = nonuser_man_choice1.count()

    nonuser_man_choice2 = nonuser_man.filter(choice_id=2 * poll_id)
    nonuser_man_choice2_count = nonuser_man_choice2.count()

    nonuser_woman = NonUserVote.objects.filter(choice__poll__pk=poll_id, gender="W")
    nonuser_woman_count = nonuser_woman.count()

    nonuser_woman_choice1 = nonuser_woman.filter(choice_id=2 * poll_id - 1)
    nonuser_woman_choice1_count = nonuser_woman_choice1.count()

    nonuser_woman_choice2 = nonuser_woman.filter(choice_id=2 * poll_id)
    nonuser_woman_choice2_count = nonuser_woman_choice2.count()

    nonuser_mbtis_count = []
    nonuser_mbtis_choice1_count = []
    nonuser_mbtis_choice2_count = []

    for mbti in mbtis:
        nonuser_mbti = NonUserVote.objects.filter(choice__poll__pk=poll_id, MBTI=mbti)
        nonuser_mbti_count = nonuser_mbti.count()
        nonuser_mbtis_count.append(nonuser_mbti_count)

        nonuser_mbti_choice1 = nonuser_mbti.filter(choice_id=2 * poll_id - 1)
        nonuser_mbti_choice1_count = nonuser_mbti_choice1.count()
        nonuser_mbtis_choice1_count.append(nonuser_mbti_choice1_count)

        nonuser_mbti_choice2 = nonuser_mbti.filter(choice_id=2 * poll_id)
        nonuser_mbti_choice2_count = nonuser_mbti_choice2.count()
        nonuser_mbtis_choice2_count.append(nonuser_mbti_choice2_count)

    total_count = user_total_count + nonuser_total_count

    total_choice1_count = user_choice1_count + nonuser_choice1_count

    total_choice2_count = user_choice2_count + nonuser_choice2_count
    total_man_count = user_man_count + nonuser_man_count

    total_man_choice1_count = user_man_choice1_count + nonuser_man_choice1_count
    total_man_choice2_count = user_man_choice2_count + nonuser_man_choice2_count

    total_woman_count = user_woman_count + nonuser_woman_count
    total_woman_choice1_count = user_woman_choice1_count + nonuser_woman_choice1_count
    total_woman_choice2_count = user_woman_choice2_count + nonuser_woman_choice2_count

    total_mbtis_count = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    total_mbtis_choice1_count = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    total_mbtis_choice2_count = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

    for i in range(16):
        total_mbtis_count[i] = user_mbtis_count[i] + nonuser_mbtis_count[i]
        total_mbtis_choice1_count[i] = (
            user_mbtis_choice1_count[i] + nonuser_mbtis_choice1_count[i]
        )
        total_mbtis_choice2_count[i] = (
            user_mbtis_choice2_count[i] + nonuser_mbtis_choice2_count[i]
        )

    choice1_percentage = int(total_choice1_count / total_count * 100)
    choice2_percentage = int(total_choice2_count / total_count * 100)

    if total_man_count != 0:
        choice1_man_percentage = int(total_man_choice1_count / total_man_count * 100)
        choice2_man_percentage = int(total_man_choice2_count / total_man_count * 100)
    else:
        choice1_man_percentage = 0
        choice2_man_percentage = 0

    if total_woman_count != 0:
        choice1_woman_percentage = int(
            total_woman_choice1_count / total_woman_count * 100
        )
        choice2_woman_percentage = int(
            total_woman_choice2_count / total_woman_count * 100
        )
    else:
        choice1_woman_percentage = 0
        choice2_woman_percentage = 0

    mbtis_dict = dict(zip(mbtis, total_mbtis_count))
    mbtis_choice1_dict = dict(zip(mbtis, total_mbtis_choice1_count))
    mbtis_choice2_dict = dict(zip(mbtis, total_mbtis_choice2_count))

    e_total_count = (
        mbtis_dict["ESTJ"]
        + mbtis_dict["ESTP"]
        + mbtis_dict["ESFJ"]
        + mbtis_dict["ESFP"]
        + mbtis_dict["ENFP"]
        + mbtis_dict["ENFJ"]
        + mbtis_dict["ENTJ"]
        + mbtis_dict["ENTP"]
    )
    e_choice1_count = (
        mbtis_choice1_dict["ESTJ"]
        + mbtis_choice1_dict["ESTP"]
        + mbtis_choice1_dict["ESFJ"]
        + mbtis_choice1_dict["ESFP"]
        + mbtis_choice1_dict["ENFP"]
        + mbtis_choice1_dict["ENFJ"]
        + mbtis_choice1_dict["ENTJ"]
        + mbtis_choice1_dict["ENTP"]
    )

    e_choice1_percentage = 0

    if e_total_count != 0:
        e_choice1_percentage = int(e_choice1_count / e_total_count * 100)
        e_choice2_percentage = 100 - e_choice1_percentage
    else:
        e_choice1_percentage = 0
        e_choice2_percentage = 0

    i_total_count = (
        mbtis_dict["ISTJ"]
        + mbtis_dict["ISTP"]
        + mbtis_dict["ISFJ"]
        + mbtis_dict["ISFP"]
        + mbtis_dict["INFP"]
        + mbtis_dict["INFJ"]
        + mbtis_dict["INTJ"]
        + mbtis_dict["INTP"]
    )
    i_choice1_count = (
        mbtis_choice1_dict["ISTJ"]
        + mbtis_choice1_dict["ISTP"]
        + mbtis_choice1_dict["ISFJ"]
        + mbtis_choice1_dict["ISFP"]
        + mbtis_choice1_dict["INFP"]
        + mbtis_choice1_dict["INFJ"]
        + mbtis_choice1_dict["INTJ"]
        + mbtis_choice1_dict["INTP"]
    )

    if i_total_count != 0:
        i_choice1_percentage = int(i_choice1_count / i_total_count * 100)
        i_choice2_percentage = 100 - i_choice1_percentage
    else:
        i_choice1_percentage = 0
        i_choice2_percentage = 0

    n_total_count = (
        mbtis_dict["INTJ"]
        + mbtis_dict["INTP"]
        + mbtis_dict["INFJ"]
        + mbtis_dict["INFP"]
        + mbtis_dict["ENFP"]
        + mbtis_dict["ENFJ"]
        + mbtis_dict["ENTJ"]
        + mbtis_dict["ENTP"]
    )
    n_choice1_count = (
        mbtis_choice1_dict["INTJ"]
        + mbtis_choice1_dict["INTP"]
        + mbtis_choice1_dict["INFJ"]
        + mbtis_choice1_dict["INFP"]
        + mbtis_choice1_dict["ENFP"]
        + mbtis_choice1_dict["ENFJ"]
        + mbtis_choice1_dict["ENTJ"]
        + mbtis_choice1_dict["ENTP"]
    )

    if n_total_count != 0:
        n_choice1_percentage = int(n_choice1_count / n_total_count * 100)
        n_choice2_percentage = 100 - n_choice1_percentage
    else:
        n_choice1_percentage = 0
        n_choice2_percentage = 0

    s_total_count = (
        mbtis_dict["ISTJ"]
        + mbtis_dict["ISTP"]
        + mbtis_dict["ISFJ"]
        + mbtis_dict["ISFP"]
        + mbtis_dict["ESFP"]
        + mbtis_dict["ESFJ"]
        + mbtis_dict["ESTJ"]
        + mbtis_dict["ESTP"]
    )
    s_choice1_count = (
        mbtis_choice1_dict["ISTJ"]
        + mbtis_choice1_dict["ISTP"]
        + mbtis_choice1_dict["ISFJ"]
        + mbtis_choice1_dict["ISFP"]
        + mbtis_choice1_dict["ESFP"]
        + mbtis_choice1_dict["ESFJ"]
        + mbtis_choice1_dict["ESTJ"]
        + mbtis_choice1_dict["ESTP"]
    )

    if s_total_count != 0:
        s_choice1_percentage = int(s_choice1_count / s_total_count * 100)
        s_choice2_percentage = 100 - s_choice1_percentage
    else:
        s_choice1_percentage = 0
        s_choice2_percentage = 0

    t_total_count = (
        mbtis_dict["INTJ"]
        + mbtis_dict["INTP"]
        + mbtis_dict["ISTJ"]
        + mbtis_dict["ISTP"]
        + mbtis_dict["ENTP"]
        + mbtis_dict["ENTJ"]
        + mbtis_dict["ESTJ"]
        + mbtis_dict["ESTP"]
    )
    t_choice1_count = (
        mbtis_choice1_dict["INTJ"]
        + mbtis_choice1_dict["INTP"]
        + mbtis_choice1_dict["ISTJ"]
        + mbtis_choice1_dict["ISTP"]
        + mbtis_choice1_dict["ENTP"]
        + mbtis_choice1_dict["ENTJ"]
        + mbtis_choice1_dict["ESTJ"]
        + mbtis_choice1_dict["ESTP"]
    )

    if t_total_count != 0:
        t_choice1_percentage = int(t_choice1_count / t_total_count * 100)
        t_choice2_percentage = 100 - t_choice1_percentage
    else:
        t_choice1_percentage = 0
        t_choice2_percentage = 0

    f_total_count = (
        mbtis_dict["INFJ"]
        + mbtis_dict["INFP"]
        + mbtis_dict["ISFJ"]
        + mbtis_dict["ISFP"]
        + mbtis_dict["ENFP"]
        + mbtis_dict["ENFJ"]
        + mbtis_dict["ESFJ"]
        + mbtis_dict["ESFP"]
    )
    f_choice1_count = (
        mbtis_choice1_dict["INFJ"]
        + mbtis_choice1_dict["INFP"]
        + mbtis_choice1_dict["ISFJ"]
        + mbtis_choice1_dict["ISFP"]
        + mbtis_choice1_dict["ENFP"]
        + mbtis_choice1_dict["ENFJ"]
        + mbtis_choice1_dict["ESFJ"]
        + mbtis_choice1_dict["ESFP"]
    )

    if f_total_count != 0:
        f_choice1_percentage = int(f_choice1_count / f_total_count * 100)
        f_choice2_percentage = 100 - f_choice1_percentage
    else:
        f_choice1_percentage = 0
        f_choice2_percentage = 0

    j_total_count = (
        mbtis_dict["INTJ"]
        + mbtis_dict["ISTJ"]
        + mbtis_dict["INFJ"]
        + mbtis_dict["ISFJ"]
        + mbtis_dict["ENFJ"]
        + mbtis_dict["ESFJ"]
        + mbtis_dict["ENTJ"]
        + mbtis_dict["ESTJ"]
    )
    j_choice1_count = (
        mbtis_choice1_dict["INTJ"]
        + mbtis_choice1_dict["ISTJ"]
        + mbtis_choice1_dict["INFJ"]
        + mbtis_choice1_dict["ISFJ"]
        + mbtis_choice1_dict["ENFJ"]
        + mbtis_choice1_dict["ESFJ"]
        + mbtis_choice1_dict["ENTJ"]
        + mbtis_choice1_dict["ESTJ"]
    )

    if j_total_count != 0:
        j_choice1_percentage = int(j_choice1_count / j_total_count * 100)
        j_choice2_percentage = 100 - j_choice1_percentage
    else:
        j_choice1_percentage = 0
        j_choice2_percentage = 0

    p_total_count = (
        mbtis_dict["INTP"]
        + mbtis_dict["ISTP"]
        + mbtis_dict["INFP"]
        + mbtis_dict["ISFP"]
        + mbtis_dict["ENFP"]
        + mbtis_dict["ESFP"]
        + mbtis_dict["ENTP"]
        + mbtis_dict["ESTP"]
    )
    p_choice1_count = (
        mbtis_choice1_dict["INTP"]
        + mbtis_choice1_dict["ISTP"]
        + mbtis_choice1_dict["INFP"]
        + mbtis_choice1_dict["ISFP"]
        + mbtis_choice1_dict["ENFP"]
        + mbtis_choice1_dict["ESFP"]
        + mbtis_choice1_dict["ENTP"]
        + mbtis_choice1_dict["ESTP"]
    )

    if p_total_count != 0:
        p_choice1_percentage = int(p_choice1_count / p_total_count * 100)
        p_choice2_percentage = 100 - p_choice1_percentage
    else:
        p_choice1_percentage = 0
        p_choice2_percentage = 0

    ctx = {
        "total_count": total_count,
        # "choice1_count": total_choice1_count,
        # "choice2_count": total_choice2_count,
        "choice1_percentage": choice1_percentage,
        "choice2_percentage": choice2_percentage,
        # "man_count": total_man_count,
        # "man_choice1_count": total_man_choice1_count,
        # "man_choice2_count": total_man_choice2_count,
        # "woman_count": total_woman_count,
        # "woman_choice1_count": total_woman_choice1_count,
        # "woman_choice2_count": total_woman_choice2_count,
        "choice1_man_percentage": choice1_man_percentage,
        "choice2_man_percentage": choice2_man_percentage,
        "choice1_woman_percentage": choice1_woman_percentage,
        "choice2_woman_percentage": choice2_woman_percentage,
        # "mbtis_count": total_mbtis_count,
        # "mbtis_choice1_count": total_mbtis_choice1_count,
        # "mbtis_choice2_count": total_mbtis_choice2_count,
        "e_choice1_percentage": e_choice1_percentage,
        "e_choice2_percentage": e_choice2_percentage,
        "i_choice1_percentage": i_choice1_percentage,
        "i_choice2_percentage": i_choice2_percentage,
        "s_choice1_percentage": s_choice1_percentage,
        "s_choice2_percentage": s_choice2_percentage,
        "n_choice1_percentage": n_choice1_percentage,
        "n_choice2_percentage": n_choice2_percentage,
        "t_choice1_percentage": t_choice1_percentage,
        "t_choice2_percentage": t_choice2_percentage,
        "f_choice1_percentage": f_choice1_percentage,
        "f_choice2_percentage": f_choice2_percentage,
        "p_choice1_percentage": p_choice1_percentage,
        "p_choice2_percentage": p_choice2_percentage,
        "j_choice1_percentage": j_choice1_percentage,
        "j_choice2_percentage": j_choice2_percentage,
        "poll": poll,
        "comments": comments,
        "user_votes": user_votes,
    }
    return render(request, template_name="vote/result.html", context=ctx)


# 비회원 투표시 MBTI 기입
def poll_nonusermbti(request, poll_id, nonuservote_id):
    if request.method == "POST":
        choice_id = request.POST.get("choice")
        selected_mbti = request.POST.get("selected_mbti")
        mbti_combination = selected_mbti

        nonuser_vote = NonUserVote.objects.get(pk=nonuservote_id)
        nonuser_vote.MBTI = mbti_combination
        nonuser_vote.save()

        if choice_id == "M":
            NonUserVote.objects.filter(pk=nonuservote_id).update(gender="M")
        if choice_id == "W":
            NonUserVote.objects.filter(pk=nonuservote_id).update(gender="W")

        poll = get_object_or_404(Poll, id=poll_id)
        context = {
            "poll": poll,
            "mbti": [],  # 여기에 MBTI 리스트 추가
            "nonuservote_id": nonuservote_id,
            "loop_time": range(0, 2),
        }
        return render(request, "vote/detail3.html", context)
    else:
        return redirect("/")


# 비회원 투표시 투표 정보 전송
def poll_nonuserfinal(request, poll_id, nonuservote_id):
    if request.method == "POST":
        selected_mbti = request.POST.get("selected_mbti")
        choice_id = request.POST.get("choice")
        NonUserVote.objects.filter(pk=nonuservote_id).update(MBTI=selected_mbti)
        calcstat_url = reverse("vote:calcstat", args=[poll_id])
        return redirect(calcstat_url)
    else:
        return redirect("/")
