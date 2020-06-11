local charset = {}

-- qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM1234567890
for i = 48,  57 do table.insert(charset, string.char(i)) end
for i = 65,  90 do table.insert(charset, string.char(i)) end
for i = 97, 122 do table.insert(charset, string.char(i)) end

function string.random(length)
    math.randomseed(os.time())
    if length > 0 then
        return string.random(length - 1) .. charset[math.random(1, #charset)]
    else
        return ""
    end
end


request = function()
    url = "/posts"
    local body = {title=string.random(10), content=string.random(100)}
    wrk.headers['Content-Type'] = "application/json"
    wrk.body = string.gsub('{"title": "$title", "content": "$content"}', "%$(%w+)", body)
    return wrk.format("POST", url)
end
